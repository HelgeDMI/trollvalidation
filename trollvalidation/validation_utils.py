import os
import gzip
import uuid
import logging
import configuration as cfg
import pyresample as pr
from zipfile import ZipFile


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
