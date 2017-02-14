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
from trollvalidation.writer import WriteNetCDF


# LOG = mp.log_to_stderr()
LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(process)d: %(levelname)s: %(asctime)s: %(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

"""
Pre-function

Used in decorator for preperaring data
"""


def prepare_test_data(temp_files, test_file):
    raise NotImplementedError


def prepare_ref_data(temp_files, ref_file, test_data, test_file):
    local_ref_file = downloader.get(ref_file, cfg.INPUT_DIR)

    # uncompress will return the unpacked shapefile in the staging directory
    local_ref_file_uncompressed, _temp_files = util.uncompress(
        local_ref_file)

    temp_files.append(local_ref_file_uncompressed)
    if temp_files:
        temp_files.append(_temp_files)

    if ref_file.endswith('.bin'):
        # run the validation step with a driver for handling binary files
        ref_data, low_lim, upp_lim = prep.handle_binfile(local_ref_file_uncompressed,
                                        test_file, test_data)
    elif ref_file.endswith('.sig'):
        # run the validation step with a driver for handling sigrid files
        ref_data, low_lim, upp_lim = prep.handle_sigfile(local_ref_file_uncompressed,
                                        test_file, test_data)
    elif ref_file.endswith('.zip'):
        # run the validation step with a driver for handling shapefiles
        ref_data, low_lim, upp_lim = prep.handle_shapefile(local_ref_file_uncompressed,
                                          test_file, test_data, temp_files)
    else:
        msg = 'I do not know how to open {0}'.format(ref_file)
        raise NotImplementedError(msg)

    return ref_data, low_lim, upp_lim


def osi_ice_conc_pre_func(ref_time, ref_file, test_file):
    """
    Functions like this are expected to return an instance of PreReturn.
    """
    temp_files = TmpFiles()

    test_data = prepare_test_data(temp_files, test_file)
    ref_data, low_lim, upp_lim = prepare_ref_data(temp_files, ref_file, test_data, test_file)

    # Dump data to files for later visualization
    dump_data(ref_time, ref_data, test_data, ref_file, test_file, low_lim, upp_lim)

    return PreReturn(temp_files, ref_data, test_data)


# def example_pre_func(ref_time, ref_file, test_file):
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
def ice_conc_val_step(ref_time, data_ref, data_test):
    run_time = datetime.now().strftime('%Y-%m-%d %H:%m:%S')
    bias_t = val_func.intermediate_bias(data_ref, data_test)
    bias_i = val_func.ice_bias(data_ref, data_test)
    bias_w = val_func.water_bias(data_ref, data_test)
    stddev_t = val_func.intermediate_std_dev(data_ref, data_test)
    stddev_i = val_func.ice_std_dev(data_ref, data_test)
    stddev_w = val_func.water_std_dev(data_ref, data_test)
    within_10pct = val_func.match_pct(data_ref, data_test, 10.)
    within_20pct = val_func.match_pct(data_ref, data_test, 20.)

    return [ref_time, run_time, bias_t, bias_i, bias_w, stddev_t, stddev_i,
            stddev_w, within_10pct, within_20pct]

# @timethis
# @around_step(pre_func=osi_ice_conc_pre_func, post_func=util.cleanup)
# def ice_conc_val_step(ref_time, data_ref, data_test):
#     run_time = datetime.now().strftime('%Y-%m-%d %H:%m:%S')
#     bias_t = val_func.intermediate_bias(data_ref, data_test)
#     bias_i = val_func.ice_bias_for_high_in_eval(data_ref, data_test)
#     bias_w = val_func.water_bias_for_low_in_eval(data_ref, data_test)
#     stddev_t = val_func.intermediate_std_dev(data_ref, data_test)
#     stddev_i = val_func.ice_std_dev_for_high_in_eval(data_ref, data_test)
#     stddev_w = val_func.water_std_dev_for_low_in_eval(data_ref, data_test)
#     within_10pct = val_func.match_pct(data_ref, data_test, 10.)
#     within_20pct = val_func.match_pct(data_ref, data_test, 20.)
#
#     return [ref_time, run_time, bias_t, bias_i, bias_w, stddev_t, stddev_i,
#             stddev_w, within_10pct, within_20pct]


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

    nh_test_files = sorted(glob(os.path.join(dir_ptn, '*NH_test*.pkl')))
    nh_ref_low_files = sorted(glob(os.path.join(dir_ptn, '*NH_ref_low*.pkl')))
    nh_ref_upp_files = sorted(glob(os.path.join(dir_ptn, '*NH_ref_upp*.pkl')))
    nh_ref_files = sorted(glob(os.path.join(dir_ptn, '*NH_ref*.pkl')))

    sh_test_files = sorted(glob(os.path.join(dir_ptn, '*SH_test*.pkl')))
    sh_ref_files = sorted(glob(os.path.join(dir_ptn, '*SH_ref*.pkl')))
    sh_ref_low_files = sorted(glob(os.path.join(dir_ptn, '*SH_ref_low*.pkl')))
    sh_ref_upp_files = sorted(glob(os.path.join(dir_ptn, '*SH_ref_upp*.pkl')))

    ds_source = [('data/NH/test', nh_test_files),
                 ('data/NH/reference', nh_ref_files),
                 ('data/NH/reference_low_lim', nh_ref_low_files),
                 ('data/NH/reference_upp_lim', nh_ref_upp_files),
                 ('data/SH/test', sh_test_files),
                 ('data/SH/reference', sh_ref_files),
                 ('data/SH/reference_low_lim', sh_ref_low_files),
                 ('data/SH/reference_upp_lim', sh_ref_upp_files)]

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

    def add_dim(data):
        shape2d = [1]
        shape2d.extend(data.shape)
        data = data.reshape(shape2d)
        return data

    path_to_output = os.path.join(config.OUTPUT_DIR, config.PICKLED_DATA)

    w = WriteNetCDF(path_to_output)

    for ds_name, files in ds_source:
        if files:
            dates, data = stack_data(files)
            w.np_array_to_nc(lat, 'lat', ('lat',),
                             unit='degrees', longname='Latitude', least_significant_digit=1, fill_value=None)

            w.np_array_to_nc(add_dim(np.array(dates)), 'time', ('time', 'lat', 'lon'))



    # hdf5 = h5py.File(path_to_output, 'w')
    # data_grp = hdf5.create_group('maps')
    # for ds_name, files in ds_source:
    #     if files:
    #         dates, data = stack_data(files)
    #         ds = data_grp.create_dataset(ds_name, data.shape, data=data.filled(),
    #                                      dtype='f', compression="gzip")
    #         ds.attrs['dates'] = np.array(dates)
    # hdf5.close()


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

    desc = config.DESCRIPTION.format('northern')
    desc_str = config.SHORT_DESCRIPTION.format('NH', date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)

    desc = config.DESCRIPTION.format('southern')
    desc_str = config.SHORT_DESCRIPTION.format('SH', date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)

    if 'PICKLED_DATA' in config.__dict__.keys():
        collect_pickled_data(config)
