import logging
import multiprocessing as mp
from datetime import datetime, date

import trollvalidation.data_preparation as prep
import trollvalidation.validation_functions as val_func
import trollvalidation.validation_utils as util
import trollvalidation.validations.configuration as cfg
from trollvalidation.data_collectors import downloader
from trollvalidation.data_collectors import tseries_generator as ts
from trollvalidation.validation_decorators import timethis, around_step, \
    around_task, PreReturn
from trollvalidation.validation_utils import TmpFiles
from trollvalidation.validation_utils import dump_data
import configuration as config


# LOG = mp.log_to_stderr()
LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def osi_ice_conc_pre_func(ref_time, eval_file, orig_file):
    """
    Functions like this are expected to return an instance of PreReturn.
    """
    temp_files = TmpFiles()

    def prepare_orig_data():
        """
        This function describes how to come from a URL identifying an input
        file to a NumPy array with the original data.

        :return: np.array | np.ma.array
        """
        if not 'thredds' in orig_file:
            # if the file is not on a thredds server download it...
            local_orig_file = downloader.get(orig_file, cfg.INPUT_DIR)
            # uncompress file if necessary
            local_orig_file_uncompressed, _ = util.uncompress(local_orig_file)
            orig_data = prep.handle_osi_ice_conc_nc_file(
                local_orig_file_uncompressed)
            temp_files.append([local_orig_file_uncompressed, local_orig_file])
        else:
            # otherwise give it directly to the Dataset reader
            orig_data = prep.handle_osi_ice_conc_nc_file(orig_file)

        return orig_data

    def prepare_eval_data(orig_data):
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

    orig_data = prepare_orig_data()
    eval_data = prepare_eval_data(orig_data)

    # Dump data to files for later visualization
    dump_data(ref_time, eval_data, orig_data, orig_file)

    return PreReturn(temp_files, eval_data, orig_data)


# def example_pre_func(ref_time, eval_file, orig_file):
#     import numpy as np
#     temp_files = TmpFiles()
#     return PreReturn(temp_files, np.array([1, 2, 3, 4]),
#                      np.array([1, 2, 3, 4]))


def collect_pickled_data():
    import os
    import re
    import h5py
    import numpy as np
    from glob import glob
    from pandas import read_pickle

    dir_ptn = '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
    dir_ptn = os.path.join(cfg.OUTPUT_DIR, dir_ptn)
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
        dates, data = zip(*dates_n_data)
        return dates, np.dstack(data)

    path_to_output = os.path.join(cfg.OUTPUT_DIR, cfg.PICKLED_DATA)
    hdf5 = h5py.File(path_to_output, 'w')
    data_grp = hdf5.create_group('maps')
    for ds_name, files in ds_source:
        dates, data = stack_data(files)
        ds = data_grp.create_dataset(ds_name, data.shape, data=data,
                                     dtype='f', compression="gzip")
        ds.attrs['dates'] = np.array(dates)
    hdf5.close()



def val_step_star(input_tuple):
    return ice_conc_val_step(*input_tuple)


@timethis
@around_step(pre_func=osi_ice_conc_pre_func, post_func=util.cleanup)
def ice_conc_val_step(ref_time, data_eval, data_orig):
    run_time = datetime.now().strftime('%Y-%m-%d %H:%m:%S')
    bias_t = val_func.total_bias(data_eval, data_orig)
    bias_i = val_func.ice_bias(data_eval, data_orig)
    bias_w = val_func.water_bias(data_eval, data_orig)
    stddev_t = val_func.total_std_dev(data_eval, data_orig)
    stddev_i = val_func.ice_std_dev(data_eval, data_orig)
    stddev_w = val_func.water_std_dev(data_eval, data_orig)
    within_10pct = val_func.match_pct(data_eval, data_orig, 10.)
    within_20pct = val_func.match_pct(data_eval, data_orig, 20.)

    return [ref_time, run_time, bias_t, bias_i, bias_w, stddev_t, stddev_i,
            stddev_w, within_10pct, within_20pct]


@around_task(pre_func=ts.generate_time_series, post_func=util.write_to_csv)
def ice_conc_val_task(file_pairs, description='', description_str=''):
    LOG.info(description)
    LOG.info(description_str)

    pool = mp.Pool(processes=mp.cpu_count())
    results = pool.map(val_step_star, file_pairs)
    pool.close()

    return results


if __name__ == '__main__':
    desc = config.DESCRIPTION.format('northern')
    desc_str = config.SHORT_DESCRIPTION.format('NH', date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)

    desc = config.DESCRIPTION.format('southern')
    desc_str = config.SHORT_DESCRIPTION.format('SH', date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)

    if 'PICKLED_DATA' in cfg.__dict__.keys():
        collect_pickled_data()
