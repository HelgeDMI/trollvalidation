import gzip
import logging
import os
import shutil
import uuid
from PIL import Image
from zipfile import ZipFile

import pandas as pd
import numpy as np
import pyresample as pr

from trollvalidation.validations import configuration as cfg

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


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
    # Delete files first and the remove directories
    # for tmp_file in tmp_files:
    #     if os.path.isfile(tmp_file):
    #         LOG.info("Cleaning up... {0}".format(tmp_file))
    #         os.remove(tmp_file)
    # for tmp_folder in tmp_files:
    #     if os.path.exists(tmp_folder):
    #         LOG.info("Cleaning up... {0}".format(tmp_folder))
    #         shutil.rmtree(tmp_folder)
    pass


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

    return pr.utils.parse_area_file('etc/areas.cfg', cfg_id)[0]


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


def dump_data(ref_time, eval_data, orig_data, orig_file):
    hemisphere = 'NH'
    if '_sh_' in os.path.basename(orig_file) or \
        '_SH_' in os.path.basename(orig_file):
        hemisphere = 'SH'

    out_path = os.path.join(cfg.OUTPUT_DIR, ref_time)

    if not os.path.exists(out_path):
        os.makedirs(out_path)

    eval_data_img = Image.fromarray(eval_data.astype(np.uint8))

    fname = os.path.join(out_path, '{0}_{1}_eval_data.bmp'.format(
        cfg.VALIDATION_ID, hemisphere))
    eval_data_img.save(fname)
    eval_data.dump(fname.replace('.bmp','.pkl'))

    orig_data_img = Image.fromarray(orig_data.astype(np.uint8))
    fname = os.path.join(out_path, '{0}_{1}_orig_data.bmp'.format(
        cfg.VALIDATION_ID, hemisphere))
    orig_data_img.save(fname)
    orig_data.dump(fname.replace('.bmp','.pkl'))
