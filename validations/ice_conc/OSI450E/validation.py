#!/usr/bin/env python

from configuration import Configuration as cfg
import ice_conc.validation as val
# from ...ice_conc.validation import validation as val
import os, sys


# sys.path.append(os.path.join(os.path.dirname(__file__)))


def prepare_test_data(temp_files, test_file):
    """
    This function describes how to come from a URL identifying an input
    file to a NumPy array with the original data.

    :return: np.array | np.ma.array
    """
    if not 'thredds' in test_file:
        # if the file is not on a thredds server download it...
        local_test_file = val.downloader.get(test_file, cfg.INPUT_DIR)
        # uncompress file if necessary
        local_test_file_uncompressed, _ = val.util.uncompress(local_test_file)
        test_data = val.prep.handle_osi_ice_conc_nc_file_osi450(
            local_test_file_uncompressed, draft='E')
        temp_files.append([local_test_file_uncompressed, local_test_file])
    else:
        # otherwise give it directly to the Dataset reader
        test_data = val.prep.handle_osi_ice_conc_nc_file_osi450(test_file, draft='E')

    return test_data

val.prepare_test_data = prepare_test_data


if __name__ == '__main__':
    val.main(cfg)
