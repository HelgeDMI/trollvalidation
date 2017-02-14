import argparse
import gzip
import json
import logging
import os
import shutil
import uuid
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pyresample as pr
from PIL import Image

from configuration import Configuration as cfg

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')


def arg_parser():
    parser = argparse.ArgumentParser(description='Validation runner')
    parser.add_argument('input_directory', metavar='input_dir', type=str, nargs='?')
    parser.add_argument('output_directory', metavar='output_dir', type=str, nargs='?')
    args = parser.parse_args()
    return args


def setup_directories(input_directory, output_directory):
    if not os.path.exists(input_directory):
        os.system('mkdir -p {0}'.format(input_directory))
    if not os.path.exists(output_directory):
        os.system('mkdir -p {0}'.format(output_directory))
        os.system('mkdir -p {0}'.format(cfg.TMP_DIR))

    for direct in [cfg.INPUT_DIR, cfg.OUTPUT_DIR]:
        try:
            os.unlink(direct)
        except OSError:
            try:
                shutil.rmtree(direct)
            except OSError:
                pass
        else:
            pass

    os.symlink(input_directory, cfg.INPUT_DIR)
    os.symlink(output_directory, cfg.OUTPUT_DIR)


class TmpFiles(object):
    """docstring for TmpFiles"""
    def __init__(self, files=[]):
        super(TmpFiles, self).__init__()
        if isinstance(files, list):
            self.tmpfiles = files
        else:
            self.tmpfiles = [files]

    def append(self, files):
        if isinstance(files, list):
            self.tmpfiles += files
        else:
            self.tmpfiles.append(files)

    def cleanup(self):
        map(os.remove, self.files)


def cleanup(_, tmp_files):
    pass
    # # Delete files first and the remove directories
    # for tmp_file in tmp_files:
    #     if os.path.isfile(tmp_file):
    #         LOG.info("Cleaning up... {0}".format(tmp_file))
    #         os.remove(tmp_file)
    # for tmp_folder in tmp_files:
    #     if os.path.exists(tmp_folder):
    #         LOG.info("Cleaning up... {0}".format(tmp_folder))
    #         shutil.rmtree(tmp_folder)


def write_to_csv(results, description_str=''):
    # prevent empty results "None" blocking the writing of CSV files
    results = filter(lambda l: l, results)

    if results:
        if cfg.CSV_HEADER:
            df = pd.DataFrame(results, index=zip(*results)[0],
                              columns=cfg.CSV_HEADER)
        else:
            df = pd.DataFrame(results, index=zip(*results)[0])
        df.to_csv(os.path.join(cfg.OUTPUT_DIR, '{0}_results.csv'.format(
            description_str)))


def get_area_def(file_handle):
    """
    This function is a utility function to read the area definition
    of corresponding to an ice concentration product.

    :param file_handle: str
        Path to an ice concentration product in NetCDF product.

    :return: AreaDefinition
        The parsed area definition corresponding to the projection
        and area extent of the product.
    """
    file_name = os.path.basename(file_handle)
    if 'NH25kmEASE2' in file_name:
        cfg_id = 'EASE2_NH'
    elif 'SH25kmEASE2' in file_name:
        cfg_id = 'EASE2_SH'
    elif 'nh_ease-125' in file_name:
        cfg_id = 'EASE_NH'
    elif 'sh_ease-125' in file_name:
        cfg_id = 'EASE_SH'
    elif 'nh_ease2-250' in file_name:
        cfg_id = 'EASE2_NH'
    elif 'sh_ease2-250' in file_name:
        cfg_id = 'EASE2_SH'
    elif 'nic_weekly_' in file_name:
        cfg_id = 'NIC_EASE_NH'
    elif 'nh_polstere-100' in file_name:
        cfg_id = 'OSISAF_NH'
    elif 'sh_polstere-100' in file_name:
        cfg_id = 'OSISAF_SH'
    # TODO: Add this case as soon as I have access to the dataset!
    # elif 'nic_weekly_' in file_name:
    #    cfg_id = 'NIC_EASE_SH'
    else:
        raise ValueError('No matching region for file {0}'.format(
            file_handle))

    return pr.utils.parse_area_file('trollvalidation/etc/areas.cfg', cfg_id)[0]


def uncompress(compressed_file, target=cfg.TMP_DIR):
    """
    This function is a utility function to uncompress NetCDF files in
    case they are given that way.

    The gzipped original is removed after decompression.

    :param product_file: str
        Path to a zipped ice concentration product in NetCDF product.

    :return: str
        The path of an uncompressed NetCDF file.
    """
    unpacked_filename, extension = os.path.splitext(compressed_file)

    if extension == '.gz':
        LOG.info('Unpacking {0}'.format(compressed_file))
        if not os.path.isfile(unpacked_filename):
            with gzip.open(compressed_file, 'rb') as packed_file:
                with open(unpacked_filename, 'wb') as unpacked_file:
                    unpacked_file.write(packed_file.read())
            # os.remove(compressed_file)
        return unpacked_filename, []
    elif extension == '.zip':
        LOG.info('Unpacking {0}'.format(compressed_file))

        tmp_id = str(uuid.uuid4())
        temporary_files_folder = os.path.join(target, tmp_id)

        with open(compressed_file, 'rb') as packed_file:
            with ZipFile(packed_file) as z:
                for name in z.namelist():
                    if name.endswith('.shp'):
                        unpacked_shapefile = os.path.join(
                            temporary_files_folder, name)
                    try:
                        z.extract(name, temporary_files_folder)
                    except Exception, e:
                        LOG.exception(e)
                        LOG.error('Could not uncompress {0}'.format(name))

        return unpacked_shapefile, [temporary_files_folder]
    else:
        return compressed_file, []


def dump_data(ref_time, ref_data, test_data, ref_file, test_file, low_lim, upp_lim):
    hemisphere = 'NH'
    if '_sh_' in os.path.basename(test_file) or \
        '_SH_' in os.path.basename(test_file):
        hemisphere = 'SH'

    out_path = os.path.join(cfg.OUTPUT_DIR, ref_time)
    if not os.path.exists(out_path):
        os.makedirs(out_path)

    datas = [('ref', ref_data), ('ref_low', low_lim), ('ref_upp', upp_lim), ('test', test_data)]
    for data_str, data in datas:

        fname_base = os.path.join(out_path, '{0}_{1}_{2}_data'.format(
            cfg.VALIDATION_ID, hemisphere, data_str))

        if data_str == 'ref' or data_str == 'test':
            data_img = Image.fromarray(data.astype(np.uint8))
            data_img.save(fname_base + '.bmp')

        data.dump(fname_base + '.pkl')

    filenames = {'test_file': test_file, 'ref_file': ref_file}
    with open(fname_base + '.json', 'w') as fp:
        json.dump(filenames, fp)
