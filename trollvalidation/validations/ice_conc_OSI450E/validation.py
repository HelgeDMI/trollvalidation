#!/usr/bin/env python

import trollvalidation.validations.template_ice_conc_OSI.validation as val
import configuration as cfg


def prepare_orig_data(temp_files, orig_file):
    """
    This function describes how to come from a URL identifying an input
    file to a NumPy array with the original data.

    :return: np.array | np.ma.array
    """
    if not 'thredds' in orig_file:
        # if the file is not on a thredds server download it...
        local_orig_file = val.downloader.get(orig_file, cfg.INPUT_DIR)
        # uncompress file if necessary
        local_orig_file_uncompressed, _ = val.util.uncompress(local_orig_file)
        orig_data = val.prep.handle_osi_ice_conc_nc_file_osi450(
            local_orig_file_uncompressed, draft='E')
        temp_files.append([local_orig_file_uncompressed, local_orig_file])
    else:
        # otherwise give it directly to the Dataset reader
        orig_data = val.prep.handle_osi_ice_conc_nc_file_osi450(orig_file, draft='E')

    return orig_data

val.prepare_orig_data = prepare_orig_data


if __name__ == '__main__':
    val.main(cfg)
