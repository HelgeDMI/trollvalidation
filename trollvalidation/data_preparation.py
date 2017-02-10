import logging
import os

import numpy as np
from netCDF4 import Dataset
import json

import validation_utils
from data_decoders.bin_reader import BINFileReader
from data_decoders.sig_reader import SIGFileReader
from data_decoders.sigrid_decoder import DecodeSIGRIDCodes



LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def handle_shapefile(shp_file, test_file, test_data, temp_files):
    """
    This function reprojects, rasterizes, and decodes NIC ice charts
    in shapefile format.

    A mixture of sigrid codes: [0, 1, 2, 13, 24, 35, 46, 57, 68, 79, 81, 91, 92, 255]
    and intervals: [0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100, 99]
    are expected

    :param shp_file:
    :param test_file:
    :return:
    """

    # reproject shapefile:
    target_area_def = validation_utils.get_area_def(test_file)
    proj_string = target_area_def.proj4_string

    reproj_filename = 'RE_{0}'.format(os.path.basename(shp_file))
    reproj_filename = os.path.join(os.path.dirname(shp_file),
                                   reproj_filename)

    cmd = 'ogr2ogr -f "ESRI Shapefile" -t_srs "{0}" {1} {2}'
    cmd = cmd.format(proj_string, reproj_filename, shp_file)
    try:
        LOG.info('Reprojecting shapefile to {0}'.format(shp_file))
        LOG.info('Executing: {0}'.format(cmd))
        os.system(cmd)
    except:
        raise Exception('ogr2ogr must be installed...')

    temp_files.append([reproj_filename,
                       reproj_filename.replace('.shp', '.shx'),
                       reproj_filename.replace('.shp', '.dbf'),
                       reproj_filename.replace('.shp', '.prj')])

    # rasterize/grid shapefile:
    layer = os.path.basename(reproj_filename).replace('.shp', '')
    area_extent = str(target_area_def.area_extent).strip('()')
    x_size = target_area_def.x_size
    y_size = target_area_def.y_size
    netcdf_file = reproj_filename.replace('.shp', '.nc')
    command = 'gdal_rasterize -l {0} -of NetCDF -init 200 -a_nodata 200 ' \
              '-where "CT IS NOT NULL" -te {1} -ts {2} {3} -ot Byte ' \
              '-a CT {4} {5}'.format(layer, area_extent, x_size, y_size,
                                     reproj_filename, netcdf_file)
    try:
        # call the actual conversion to NetCDF file
        LOG.info('Rasterizing shapefile to {0}'.format(netcdf_file))
        LOG.info('Executing: {0}'.format(cmd))
        os.system(command)
    except:
        raise Exception('gdal_rasterize must be installed...')

    temp_files.append(netcdf_file)

    # read NetCDF file
    dataset = Dataset(netcdf_file)
    # on my computer the image needs to be flipped upside down...
    # TODO: check if this is also necessary on other computers
    ref_data = np.flipud(dataset.variables['Band1'][:]) #.astype(np.uint8))
    # finally convert the sigrid ice codes to ice concentrations in %
    decoder = DecodeSIGRIDCodes()
    LOG.info('Decoding shape file with values: {}'.format(np.unique(ref_data, return_counts=False)))
    ref_data, low_lim, upp_lim = decoder.sigrid_decoding(ref_data, test_data)

    return ref_data, low_lim, upp_lim


def handle_binfile(bin_file, test_file, test_data):

    bin_reader = BINFileReader()
    ref_file_data = bin_reader.read_data(bin_file, test_file)

    decoder = DecodeSIGRIDCodes()
    LOG.info('Decoding bin file with values: {}'.format(np.unique(ref_file_data, return_counts=False)))
    ref_data, low_lim, upp_lim = decoder.easegrid_decoding(ref_file_data, test_data)
    return ref_data


def handle_sigfile(sig_file, test_file, test_data):

    sig_reader = SIGFileReader()
    ref_file_data = sig_reader.read_data(sig_file, test_file)

    decoder = DecodeSIGRIDCodes()
    LOG.info('Decoding sig file with values: {}'.format(np.unique(ref_file_data, return_counts=False)))
    ref_data = decoder.sigrid_decoding(ref_file_data, test_data)
    return ref_data


# def handle_osi_ice_conc_nc_file(input_file):
#     """
#     This function reads the variable 'ice_conc' from an ice
#     concentration product in NetCDF format.
#
#     It filters out all values, which are, based on the field
#     'status_flag', not a proper ice concentration value.
#
#     :param input_file: str
#         Path to an ice concentration product in NetCDF product.
#
#     :return: np.array|np.ma.array
#         The 'matrix' of ice concentration values. It is expected for
#         this validation that the values are in the range of [0..100]
#     """
#     try:
#         dataset = Dataset(input_file)
#     except IOError, e:
#         LOG.info('File: {} not found'.format(input_file))
#         LOG.exception(e)
#     ice_conc = dataset.variables['ice_conc'][0].data[:]
#     status_flag = dataset.variables['status_flag'][0][:]
#     mask_conc = np.logical_or(ice_conc < 0, ice_conc > 100)
#     ice_conc = np.ma.array(ice_conc, mask=mask_flags)
#     return ice_conc

def handle_osi_ice_conc_nc_file(input_file):
    """
    This function reads the variable 'ice_conc' from an ice
    concentration product in NetCDF format.

    It filters out all values, which are, based on the field
    'status_flag', not a proper ice concentration value.

    :param input_file: str
        Path to an ice concentration product in NetCDF product.

    :return: np.array|np.ma.array
        The 'matrix' of ice concentration values. It is expected for
        this validation that the values are in the range of [0..100]
    """
    try:
        dataset = Dataset(input_file)
    except IOError:
        LOG.info('File: {} not found'.format(input_file))
        raise
    ice_conc = dataset.variables['ice_conc'][0].data[:]
    status_flag = dataset.variables['status_flag'][0][:]
    ice_conc = np.ma.array(ice_conc, mask=(status_flag != 0))
    ice_conc = np.ma.masked_outside(ice_conc, -0.01, 100.01)
    return ice_conc


def handle_osi_ice_conc_nc_file_osi450(input_file, draft):
    """
    This function reads the variable 'ice_conc' from an ice
    concentration product in NetCDF format.

    It filters out all values, which are, based on the field
    'status_flag', not a proper ice concentration value.

    :param input_file: str
        Path to an ice concentration product in NetCDF product.

    :return: np.array|np.ma.array
        The 'matrix' of ice concentration values. It is expected for
        this validation that the values are in the range of [0..100]
    """
    try:
        dataset = Dataset(input_file)
    except IOError:
        LOG.info('File: {} not found'.format(input_file))
        raise
    ice_conc = dataset.variables['ice_conc'][0].data[:]
    status_flag = dataset.variables['status_flag'][0][:]
    if draft == 'C':
        mask_flags = np.logical_or.reduce((status_flag & 1 == 1, status_flag & 2 == 2, status_flag & 8 == 8))
    elif draft == 'E':
        mask_flags = np.logical_or.reduce(
            (status_flag & 32 == 32, status_flag & 64 == 64, status_flag & 128 == 128,
             status_flag & 2 == 2, status_flag & 8 == 8, status_flag & 1 == 1))
    ice_conc = np.ma.array(ice_conc, mask=mask_flags)
    ice_conc = np.ma.masked_outside(ice_conc, -0.01, 100.01)
    return ice_conc
