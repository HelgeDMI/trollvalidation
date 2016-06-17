import os
import shutil
import logging

import pandas as pd
import configuration as cfg
import multiprocessing as mp
import validation_utils as util
import data_preparation as prep
import validation_functions as val_func

from datetime import datetime, date
from collections import namedtuple
from validation_utils import TmpFiles
from validation_decorators import timethis, around_step, around_task
from data_collectors import downloader
from data_collectors import tseries_generator as ts


# LOG = mp.log_to_stderr()
LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


PreReturn = namedtuple('PreReturn', 'tmpfiles data_eval data_orig')


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
        local_orig_file = downloader.get(orig_file, cfg.INPUT_DIR)
        # uncompress file if necessary
        local_orig_file_uncompressed = util.uncompress(local_orig_file)
        orig_data = prep.handle_osi_ice_conc_nc_file(
            local_orig_file_uncompressed)

        temp_files.append([local_orig_file_uncompressed, local_orig_file])

        return orig_data

    def prepare_eval_data():
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
                                            orig_file)
        elif eval_file.endswith('.sig'):
            # run the validation step with a driver for handling sigrid files
            eval_data = prep.handle_sigfile(local_eval_file_uncompressed,
                                            orig_file)
        elif eval_file.endswith('.zip'):
            # run the validation step with a driver for handling shapefiles
            eval_data = prep.handle_shapefile(local_eval_file_uncompressed,
                                              orig_file, temp_files)
        else:
            msg = 'I do not know how to open {0}'.format(eval_file)
            raise NotImplementedError(msg)

        return eval_data

    return PreReturn(temp_files, prepare_eval_data(), prepare_orig_data())


def example_pre_func(ref_time, eval_file, orig_file):
    import numpy as np
    temp_files = TmpFiles()
    return PreReturn(temp_files, np.array([1, 2, 3, 4]), np.array([1, 2, 3, 4]))


def cleanup(_, tmp_files):
    # Delete files first and the remove directories
    for tmp_file in tmp_files:
        if os.path.isfile(tmp_file):
            LOG.info("Cleaning up... {0}".format(tmp_file))
            os.remove(tmp_file)
    for tmp_folder in tmp_files:
        if os.path.exists(tmp_folder):
            LOG.info("Cleaning up... {0}".format(tmp_folder))
            shutil.rmtree(tmp_folder)


def write_to_csv(results, description_str=''):
    if cfg.CSV_HEADER:
        df = pd.DataFrame(results, index=zip(*results)[0],
                          columns=cfg.CSV_HEADER)
    else:
        df = pd.DataFrame(results, index=zip(*results)[0])
    df.to_csv(os.path.join(cfg.OUTPUT_DIR, '{0}_results.csv'.format(
        description_str)))


def ice_conc_val_step_star(input_tuple):
    return ice_conc_val_step(*input_tuple)


@timethis
@around_step(pre_func=example_pre_func, post_func=cleanup)
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


@around_task(pre_func=ts.generate_time_series, post_func=write_to_csv)
def ice_conc_val_task(file_pairs, description='', description_str=''):
    LOG.info(description)
    LOG.info(description_str)

    pool = mp.Pool(processes=mp.cpu_count())
    results = pool.map(ice_conc_val_step_star, file_pairs)
    pool.close()

    return results


if __name__ == '__main__':

    desc = 'Comparison of NIC ice charts and OSI-409 products for northern ' \
           'hemisphere'
    desc_str = 'OSI401_validation_NH_{0}'.format(date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)

    desc = 'Comparison of NIC ice charts and OSI-409 products for southern ' \
           'hemisphere'
    desc_str = 'OSI401_validation_SH_{0}'.format(date.today())
    ice_conc_val_task(description=desc, description_str=desc_str)
