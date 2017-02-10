from trollvalidation.validations.template_ice_conc_OSI.configuration import *
from trollvalidation.validations.template_ice_conc_OSI import configuration as cfg

print('CONFIG OSI409')

VALIDATION_ID = 'OSI409'
DESCRIPTION = 'Comparison of NIC ice charts and OSI-409 products for {0}' \
' hemisphere'
SHORT_DESCRIPTION = 'OSI409_validation_{0}_{1}'  # hemisphere, date
PICKLED_DATA = 'OSI409_val_data.hdf5'

cfg.METNO_THREDDS_DOWNL['remote_dir_f_pattern'] = 'thredds/dodsC/metusers/sicci_shared/osisaf/v1.2_EASE2/{0}/{1}/'\
                                              'ice_conc_{2}h_ease2-250_cdr-v1p2_{3}1200.nc'
METNO_THREDDS_DOWNL = cfg.METNO_THREDDS_DOWNL

