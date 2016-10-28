import logging
import os

import numpy as np
from netCDF4 import Dataset

import validation_utils
from data_decoders.bin_reader import BINFileReader
from data_decoders.sig_reader import SIGFileReader
from data_decoders.sigrid_decoder import DecodeSIGRIDCodes


LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def handle_shapefile(shp_file, orig_file, orig_data, temp_files):
    """
    This function reprojects, rasterizes, and decodes NIC ice charts
    in shapefile format.

    :param shp_file:
    :param orig_file:
    :return:
    """

    # reproject shapefile:
    target_area_def = validation_utils.get_area_def(orig_file)
    proj_string = target_area_def.proj4_string

    reproj_filename = 'RE_{0}'.format(os.path.basename(shp_file))
    reproj_filename = os.path.join(os.path.dirname(shp_file),
                                   reproj_filename)

    cmd = 'ogr2ogr -f "ESRI Shapefile" -t_srs "{0}" {1} {2}'
    cmd = cmd.format(proj_string, reproj_filename, shp_file)
    try:
        LOG.info('Reprojecting shapefile to {0}'.format(shp_file))
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
        os.system(command)
    except:
        raise Exception('gdal_rasterize must be installed...')

    temp_files.append(netcdf_file)

    # read NetCDF file
    dataset = Dataset(netcdf_file)
    # on my computer the image needs to be flipped upside down...
    # TODO: check if this is also necessary on other computers
    eval_data = np.flipud(dataset.variables['Band1'][:].astype(np.uint8))
    print(np.flipud(dataset.variables['Band1'][:].min(), np.flipud(dataset.variables['Band1'][:].max())
    print(eval_data.min(), eval_data.max())
    # finally convert the sigrid ice codes to ice concentrations in %
    decoder = DecodeSIGRIDCodes()
    eval_data = decoder.sigrid_decoding(eval_data, orig_data)

    return eval_data


def handle_binfile(bin_file, orig_file, orig_data):
    bin_reader = BINFileReader()
    eval_file_data = bin_reader.read_data(bin_file, orig_file)

    decoder = DecodeSIGRIDCodes()
    eval_data = decoder.sigrid_decoding(eval_file_data, orig_data)
    return eval_data


def handle_sigfile(sig_file, orig_file, orig_data):
    sig_reader = SIGFileReader()
    eval_file_data = sig_reader.read_data(sig_file, orig_file)

    decoder = DecodeSIGRIDCodes()
    eval_data = decoder.sigrid_decoding(eval_file_data, orig_data)
    return eval_data


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
    dataset = Dataset(input_file)
    ice_conc = dataset.variables['ice_conc'][0].data[:]
    status_flag = dataset.variables['status_flag'][0][:]
    ice_conc = np.ma.array(ice_conc, mask=(status_flag != 0))
    return ice_conc
