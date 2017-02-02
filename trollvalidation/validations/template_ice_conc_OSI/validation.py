#!/usr/bin/env python

import logging
import multiprocessing as mp
from datetime import datetime, date
from glob import glob
import numpy.ma as ma
import shutil
import os

import trollvalidation.data_preparation as prep
import trollvalidation.validation_functions as val_func
import trollvalidation.validation_utils as util
from trollvalidation.data_collectors import downloader
from trollvalidation.data_collectors import tseries_generator as ts
from trollvalidation.validation_decorators import timethis, around_step, \
    around_task, PreReturn
from trollvalidation.validation_utils import TmpFiles
from trollvalidation.validation_utils import dump_data
import configuration as cfg


# LOG = mp.log_to_stderr()
LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(process)d: %(levelname)s: %(asctime)s: %(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

"""
Pre-function

Used in decorator for preperaring data
"""


def prepare_orig_data(temp_files, orig_file):
    raise NotImplementedError


def prepare_eval_data(temp_files, eval_file, orig_data, orig_file):
    local_eval_file = downloader.get(eval_file, cfg.INPUT_DIR)

    # uncompress will return the unpacked shapefile in the staging directory
    local_eval_file_uncompressed, _temp_files = util.uncompress(
        local_eval_file)

    temp_files.append(local_eval_file_uncompressed)
    if temp_files:
        temp_files.append(_temp_files)

    if eval_file.endswith('.bin'):
        # run the validation step with a driver for handling binary files
        eval_data = prep.handle_binfile(local_eval_file_uncompressed,
                                        orig_file, orig_data)
    elif eval_file.endswith('.sig'):
        # run the validation step with a driver for handling sigrid files
        eval_data = prep.handle_sigfile(local_eval_file_uncompressed,
                                        orig_file, orig_data)
    elif eval_file.endswith('.zip'):
        # run the validation step with a driver for handling shapefiles
        eval_data = prep.handle_shapefile(local_eval_file_uncompressed,
                                          orig_file, orig_data, temp_files)
    else:
        msg = 'I do not know how to open {0}'.format(eval_file)
        raise NotImplementedError(msg)

    return eval_data


def osi_ice_conc_pre_func(ref_time, eval_file, orig_file):
    """
    Functions like this are expected to return an instance of PreReturn.
    """
    temp_files = TmpFiles()

    orig_data = prepare_orig_data(temp_files, orig_file)
    eval_data = prepare_eval_data(temp_files, eval_file, orig_data, orig_file)

    # Dump data to files for later visualization
    dump_data(ref_time, eval_data, orig_data, eval_file, orig_file)

    return PreReturn(temp_files, eval_data, orig_data)


# def example_pre_func(ref_time, eval_file, orig_file):
#     import numpy as np
#     temp_files = TmpFiles()
#     return PreReturn(temp_files, np.array([1, 2, 3, 4]),
#                      np.array([1, 2, 3, 4]))


def val_step_star(input_tuple):
    return ice_conc_val_step(*input_tuple)


"""
Decorate functions
"""


@timethis
@around_step(pre_func=osi_ice_conc_pre_func, post_func=util.cleanup)
def ice_conc_val_step(ref_time, data_eval, data_orig):
    run_time = datetime.now().strftime('%Y-%m-%d %H:%m:%S')
    bias_t = val_func.intermediate_bias(data_eval, data_orig)
    bias_i = val_func.ice_bias_for_high_in_eval(data_eval, data_orig)
    bias_w = val_func.water_bias_for_low_in_eval(data_eval, data_orig)
    stddev_t = val_func.intermediate_std_dev(data_eval, data_orig)
    stddev_i = val_func.ice_std_dev_for_high_in_eval(data_eval, data_orig)
    stddev_w = val_func.water_std_dev_for_low_in_eval(data_eval, data_orig)
    within_10pct = val_func.match_pct(data_eval, data_orig, 10.)
    within_20pct = val_func.match_pct(data_eval, data_orig, 20.)

    return [ref_time, run_time, bias_t, bias_i, bias_w, stddev_t, stddev_i,
            stddev_w, within_10pct, within_20pct]


@around_task(pre_func=ts.generate_time_series, post_func=util.write_to_csv)
def ice_conc_val_task(file_pairs, description='', description_str=''):
    LOG.info(description)
    LOG.info(description_str)

    # results = [val_step_star(file_pairs[0])]
    pool = mp.Pool(processes=mp.cpu_count())
    results = pool.map(val_step_star, file_pairs)
    pool.close()

    return results


"""
Postprocessing
"""


def collect_pickled_data(config):
    import os
    import re
    import h5py
    import numpy as np
    from glob import glob
    from pandas import read_pickle

    dir_ptn = '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    dir_ptn = os.path.join(config.OUTPUT_DIR, dir_ptn)
    nh_orig_files = sorted(glob(os.path.join(dir_ptn, '*NH_orig*.pkl')))
    nh_eval_files = sorted(glob(os.path.join(dir_ptn, '*NH_eval*.pkl')))
    sh_orig_files = sorted(glob(os.path.join(dir_ptn, '*SH_orig*.pkl')))
    sh_eval_files = sorted(glob(os.path.join(dir_ptn, '*SH_eval*.pkl')))

    ds_source = [('data/NH/satellite', nh_orig_files),
                 ('data/NH/reference', nh_eval_files),
                 ('data/SH/satellite', sh_orig_files),
                 ('data/SH/reference', sh_eval_files)]

    def read_pkl(path):
        date_str = re.search('\d{4}-\d{2}-\d{2}', path).group(0)
        return date_str, read_pickle(path)

    def stack_data(file_list):
        dates_n_data = map(read_pkl, file_list)
        dates, datas = zip(*dates_n_data)
        try:
            masks = np.dstack((d.mask for d in datas))
        except AttributeError:
            masks = np.dstack((np.zeros(d.shape) for d in datas))
        datas = np.dstack(datas)
        datas = ma.array(datas, mask=masks, fill_value=np.nan)
        return dates, datas

    path_to_output = os.path.join(config.OUTPUT_DIR, config.PICKLED_DATA)
    hdf5 = h5py.File(path_to_output, 'w')
    data_grp = hdf5.create_group('maps')
    for ds_name, files in ds_source:
        if files:
            dates, data = stack_data(files)
            ds = data_grp.create_dataset(ds_name, data.shape, data=data.filled(),
                                         dtype='f', compression="gzip")
            ds.attrs['dates'] = np.array(dates)
    hdf5.close()


def cleanup(config):
    try:
        os.remove(config.METNO_THREDDS_DOWNL['glob_file'])
    except OSError:
        pass

    tmp_dirs = (d for d in glob(os.path.join(cfg.TMP_DIR, '*')) if os.path.isdir(d))
    for tmp_dir in tmp_dirs:
        shutil.rmtree(tmp_dir)


def main(config):
    cleanup(config)

    args = util.arg_parser()
    util.setup_directories(args.input_directory, args.output_directory)

    desc = cfg.DESCRIPTION.format('northern')
    desc_str = cfg.SHORT_DESCRIPTION.format('NH', date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)

    desc = cfg.DESCRIPTION.format('southern')
    desc_str = cfg.SHORT_DESCRIPTION.format('SH', date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)

    if 'PICKLED_DATA' in config.__dict__.keys():
        collect_pickled_data(config)
