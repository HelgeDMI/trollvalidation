import os
import datetime
import pandas as pd

# for OSI-450 validation
YEARS_OF_INTEREST = range(1992, 1994)
# for OSI-401 validation
# YEARS_OF_INTEREST = [1996]

CSV_HEADER = ['reference_time', 'run_time', 'total_bias', 'ice_bias',
              'water_bias', 'total_stddev', 'ice_stddev', 'water_stddev',
              'within_10pct', 'within_20pct']

START_YEAR = min(YEARS_OF_INTEREST)
END_YEAR = max(YEARS_OF_INTEREST)
if END_YEAR == START_YEAR:
    END_YEAR += 1

BASE_PATH = os.path.join(os.path.expanduser('~/'), 'validation', 'data')
INPUT_DIR = os.path.join(BASE_PATH, 'input')
# for OSI-409 validation
OUTPUT_DIR = os.path.join(BASE_PATH, 'output')
# for OSI-401 validation
# OUTPUT_DIR = os.path.join(BASE_PATH, 'output', 'OSI-401-a')
TMP_DIR = os.path.join(BASE_PATH, 'input', 'tmp')

AREAS = 'etc/areas.cfg'
DESCRIPTION = 'Comparison of NIC ice charts and OSI-450 products for {0}' \
' hemisphere'
SHORT_DESCRIPTION = 'OSI450_validation_{0}_{1}'  # hemisphere, date
PICKLED_DATA = 'OSI450_val_data.hdf5'

# for OSI-409 validation
METNO_DOWNL = {
    'protocol': 'ftp://',
    'host': 'osisaf.met.no',
    'remote_dir_f_pattern': 'reprocessed/ice/conc/v1p2/*/*/*ease*.nc.gz',
    'remote_date_pattern': (r'\d{12}', '%Y%m%d%H%M'),
    'glob_file': os.path.join(TMP_DIR, 'metno_files.json')
}

# for OSI-401 validation
# METNO_DOWNL = {
#     'protocol': 'ftp://',
#     'host': 'osisaf.met.no',
#     'remote_dir_f_pattern': 'archive/ice/conc/*/*/*_polstere-100_multi_*.nc',
#     'remote_date_pattern': (r'\d{12}', '%Y%m%d%H%M'),
#     'glob_file': os.path.join(TMP_DIR, 'metno_files.json')
# }


NIC_BIN_DOWNL = {
    'protocol': 'ftp://',
    'host': 'sidads.colorado.edu',
    'remote_dir_f_pattern':
        'pub/DATASETS/NOAA/G02172/weekly/nic_weekly_*_tot.v0.bin',
    'remote_date_pattern': (r'\d{4}_\d{2}_\d{2}', '%Y_%m_%d'),
    'glob_file': os.path.join(TMP_DIR, 'nic_bin_files.json')
}

NIC_SIG_DOWNL = {
    'protocol': 'http://',
    'host': 'wdc.aari.ru',
    'remote_dir_f_pattern': 'datasets/d0001/south/nic/*/*.sig',
    'remote_date_pattern': (r'\d{6}', '%Y%W'),
    'glob_file': os.path.join(TMP_DIR, 'nic_sig_files.json'),
}

NIC_SHP_DOWNL = {
    'scrape': True,
    'protocol': 'http://',
    'host': 'www.natice.noaa.gov',
    'remote_html_path': {
        'nh':
            'products/weekly_products.html?oldarea=Arctic&area=Arctic&'
            'oldformat=Shapefiles&format=Shapefiles&month0=Jan&day0=01&'
            'year0=2006&month1=Jan&day1=01&year1={0}&subareas='
            'Hemispheric'.format(datetime.datetime.now().year + 1),
        'sh':
            'products/weekly_products.html?oldarea=Antarctic&area=Antarctic&'
            'oldformat=Shapefiles&format=Shapefiles&month0=Jan&day0=01&'
            'year0=2006&month1=Jan&day1=01&year1={0}&subareas='
            'Hemispheric'.format(datetime.datetime.now().year + 1)
    },
    'remote_file_pattern': {
        'nh': 'pub/weekly/arctic/{0}/shapefiles/hemispheric/arctic{1}.zip',
        'sh': 'pub/weekly/antarctic/{0}/shapefiles/hemispheric/antarc{1}.zip'
    },
    'remote_link_pattern': {
        'nh': r'href\s?=\s?".*arctic\d{6}.zip',
        'sh': r'href\s?=\s?".*antarc\d{6}.zip',
    },
    'remote_date_pattern': (r'\d{6}', '%y%m%d'),
    'glob_file': os.path.join(TMP_DIR, 'nic_shp_files.json')
}

# http://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/conc/2016/09/ice_conc_sh_polstere-100_multi_201609211200.nc
METNO_THREDDS_DOWNL = {
    'generate':
        pd.date_range('1/1/{0} 12:00'.format(START_YEAR),
                      '1/1/{0} 12:00'.format(END_YEAR), freq='D'),
    'protocol': 'http://',
    'host': 'thredds.met.no',
    'remote_dir_f_pattern':
    'thredds/dodsC/metusers/sicci_shared/v2.0draftB/{0}/{1}/' \
    'ice_conc_{2}h_ease2-250_cdr-v2p0_{3}1200.nc',
    'remote_date_pattern': (r'\d{12}', '%Y%m%d%H%M'),
    'glob_file': os.path.join(TMP_DIR, 'metno_thredds_files.json')
}


if not os.path.exists(INPUT_DIR):
    os.system('mkdir -p {0}'.format(INPUT_DIR))
if not os.path.exists(OUTPUT_DIR):
    os.system('mkdir -p {0}'.format(OUTPUT_DIR))
if not os.path.exists(TMP_DIR):
    os.system('mkdir -p {0}'.format(TMP_DIR))

import apt
cache = apt.Cache()
if not cache['gdal-bin'].is_installed:
    raise Exception('You have to have "gdal-bin" installed. Do "apt-get '
                    'install gdal-bin"!')
if not cache['lftp'].is_installed:
    raise Exception('You have to have "lftp" installed. Do "apt-get '
                    'install lftp"!')
