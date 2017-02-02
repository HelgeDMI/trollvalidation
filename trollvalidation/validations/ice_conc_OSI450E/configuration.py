from trollvalidation.validations.template_ice_conc_OSI.configuration import *

print('CONFIG OSI450E')

# YEARS_OF_INTEREST = range(1972, 2017)
YEARS_OF_INTEREST = [2006]

VALIDATION_ID = 'OSI_450E'
DESCRIPTION = 'Comparison of NIC ice charts and OSI-450 Draft E products for {0}' \
' hemisphere'
SHORT_DESCRIPTION = 'OSI450E_validation_{0}_{1}'  # hemisphere, date
PICKLED_DATA = 'OSI450E_val_data.hdf5'

START_YEAR = min(YEARS_OF_INTEREST)
END_YEAR = max(YEARS_OF_INTEREST)
if END_YEAR == START_YEAR:
    END_YEAR += 1

# http://thredds.met.no/thredds/dodsC/osisaf/met.no/ice/conc/2016/09/ice_conc_sh_polstere-100_multi_201609211200.nc
METNO_THREDDS_DOWNL = {
    'generate':
        pd.date_range('1/1/{0} 12:00'.format(START_YEAR),
                      '1/1/{0} 12:00'.format(END_YEAR), freq='D'),
    'protocol': 'http://',
    'host': 'thredds.met.no',
    'remote_dir_f_pattern':
    'thredds/dodsC/metusers/sicci_shared/osisaf/v2.0draftE/{0}/{1}/'\
    'ice_conc_{2}h_ease2-250_cdr-v2p0_{3}1200.nc',
    'remote_date_pattern': (r'\d{12}', '%Y%m%d%H%M'),
    'glob_file': os.path.join(TMP_DIR, 'metno_thredds_files.json')
}
