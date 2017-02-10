from trollvalidation.validations.template_ice_conc_OSI.configuration import *
from trollvalidation.validations.template_ice_conc_OSI import configuration as cfg

print('CONFIG OSI450E')

VALIDATION_ID = 'OSI_450E'
DESCRIPTION = 'Comparison of NIC ice charts and OSI-450 Draft E products for {0}' \
' hemisphere'
SHORT_DESCRIPTION = 'OSI450E_validation_{0}_{1}'  # hemisphere, date
PICKLED_DATA = 'OSI450E_val_data.hdf5'

cfg.METNO_THREDDS_DOWNL['remote_dir_f_pattern'] = 'thredds/dodsC/metusers/sicci_shared/osisaf/v2.0draftE/{0}/{1}/' \
                                              'ice_conc_{2}h_ease2-250_cdr-v2p0_{3}1200.nc'
METNO_THREDDS_DOWNL = cfg.METNO_THREDDS_DOWNL
