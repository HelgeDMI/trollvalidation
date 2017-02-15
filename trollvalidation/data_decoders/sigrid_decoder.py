import numpy as np
from numpy import ma
import logging

"""

## Codes and Values for Ice Concentrations

See https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid

Ice Concentration from Egg Code 	SIGRID Code 	EASE-Grid Product Value for Concentration
-------------------------------     -----------     -----------------------------------------
Ice free 	                            00 	                     0
Less than 1/10 (open water) 	        01 	                     5
Bergy water 	                        02  	                 5
1/10 	                                10                   	10
2/10 	                                20                  	20
3/10 	                                30                     	30
4/10 	                                40                   	40
5/10 	                                50                   	50
6/10 	                                60                   	60
7/10 	                                70                   	70
8/10 	                                80                   	80
9/10 	                                90                   	90
More than 9/10, less than 10/10 	    91                   	95
10/10 	                                92                   	100

Concentration Intervals
(Cl = lowest concentration in interval
(Ch = highest concentration in interval)	ClCh
Examples:
1/10 - 3/10	                            13	                    20
4/10 - 6/10	                            46	                    50
7/10 - 9/10	                            79	                    80
7/10 - 10/10	                        71                  	85 # How does this follow?
----------------------------------------------------------------------------------------------------
Table 9.

Undetermined                            99                      255 # Assuming 255 in undetermined,
                                                                    # but not verified

EASE-Grid Climatology Data File Values:
Ice concentration (percent) or frequency of occurrence (percent) (in multiples of 5)

## Description of EASE Grid Format
https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid/#format

## Description of GRIDDED SIGRID FORMAT FOR SEA ICE
http://www.natice.noaa.gov/products/sigrid.html

Accuracy and Precision
The accuracy and precision of the original charts is not known with certainty. Partington (2003)
cites +/-5 percent to +/-10 percent as the accuracy of ice concentration estimates. Total ice
concentration for an individual polygon is recorded in a range. That range is expressed in
tenths. The mean value of that range is used in the EASE-Grid files. Thus, the precision can
vary from grid cell to grid cell depending on the range with which the concentration was
originally charted.


"""

LOG = logging.getLogger(__name__)


class DecodeSIGRIDCodes(object):

    @staticmethod
    def valid_values_check(data_ref, expected):
        for v in np.unique(data_ref):
            if (not v in expected) and (not isinstance(v, np.ma.core.MaskedConstant)):
                    raise ValueError('Unexpected value in file: {0}'.format(v))

    def intervals_to_sigrid_codes(self, data_ref):
        """
        Convert the bin intervals to the corresponding sigrid codes
        For documentation on the bin files:
        https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid/#format
        """
        expected = np.append(np.arange(0, 101, 5), 5)
        self.valid_values_check(data_ref, expected)
        de = data_ref
        # condition_choices is [(de == concentration_interval, sigrid_code), ...]
        condition_choice = [
            (de == 99, 255),
            (de == 05,  01),  # It can also be 2.
            (de == 95,  91),
            (de == 100, 92),
            (de == 00,  00),
            ((de % 10 == 0), de, de)
            ]
        condition, choice = zip(*condition_choice)
        codes = np.select(condition, choice, default=de)

        if isinstance(de, np.ma.core.MaskedArray):
            codes = np.ma.array(codes, mask=de.mask)

        return codes

    def sigrid_decoding(self, data_ref, data_test):
        data_ref = data_ref.astype(int)

        # Check that there are no unexpected values

        expected = [00, 01, 02, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25,
                    26, 27, 28, 29, 30, 31, 34, 35, 36, 37, 38, 39, 40, 41, 45, 46, 47, 48,
                    49, 50, 51, 56, 57, 58, 59, 60, 61, 67, 68, 69, 70, 71, 78, 79, 80, 81,
                    89, 90, 91, 92, 255]
        self.valid_values_check(data_ref, expected)

        # Convert the sigrid codes to upper and lower limits of ice concentration

        dr = data_ref
        cl = 10 * (dr // 10)  # lower code: 1st digit * 10
        cu = 10 * (dr % 10)   # upper code: 2nd digit * 10
        condition_choices = [
            (dr == 255, np.nan, np.nan),
            (dr == 00, 0,  0),
            (dr == 01, 0, 10),
            (dr == 02, 0, 10),  # TODO: Check this
            (dr == 92, 100, 100),
            (cu == 10, cl, 100),        # 21, 31, 41, 51, 61, 71, 81, 91
            (cu == 00, dr, dr),         # 10, 20, 30, 40, 50, 60, 70, 80, 90
            (~(dr % 10 == 0), cl, cu)   # 12, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25,
                                        # 26, 27, 28, 29, 34, 35, 36, 37, 38, 39, 45,
                                        # 46, 47, 48, 49, 56, 57, 58, 59, 67, 68, 69,
                                        # 78, 79, 89
        ]
        condition, lower_limit, upper_limit = zip(*condition_choices)
        lower_limits = np.select(condition, lower_limit, default=-128)
        upper_limits = np.select(condition, upper_limit, default=-128)

        if (-128 in lower_limits) or (-128 in upper_limits):
            raise ValueError('Values {} not decoded'.format(dr[(lower_limits == -128) | (upper_limits == -128)]))

        try:
            assert np.any((upper_limits >= lower_limits) | np.isnan(upper_limits) | np.isnan(lower_limits))
        except:
            u, l = upper_limit[upper_limits < lower_limits], lower_limits[upper_limits < lower_limits]
            raise ValueError('Sigrid decoding invalid: {0} (upper) < {1} (lower)'.format(u, l))

        # The variable 'reference' is the closet possible value of the NIC data to data_test, given that the NIC data
        # can be an interval. So, if the NIC sigrid codes specify limit, they converted to a reference as follows:
        #   * if data_test is within the bounds of the NIC limits, reference = data_test
        #   * otherwise, reference is equal to the closest limit of the NIC interval.
        # If the NIC codes are specific values, rather that limits, 'reference' is equal to data_ref

        dt, ll, ul = data_test, lower_limits, upper_limits
        # 'condition_choice' is a follows: [(interval, choice),...]

        condition_choice = [((dt >= ll) & (dt <= ul), dt),
                             (dt < ll,                ll),
                             (dt > ul,                ul)]
        cond, choice = zip(*condition_choice)
        reference = np.select(cond, choice, default=np.nan)

        if np.any(np.isnan(reference)):
            LOG.info('The file contains undetermined values')

        reference = ma.masked_invalid(reference)
        if isinstance(data_ref, np.ma.core.MaskedArray):
            reference = ma.array(reference, mask=data_ref.mask)

        return reference, lower_limits, upper_limits

    def easegrid_decoding(self, data_ref, product_file_data):
        data_ref = data_ref.astype(int)
        sigrid_codes = self.intervals_to_sigrid_codes(data_ref)
        reference, low_lim, upp_lim = self.sigrid_decoding(sigrid_codes, product_file_data)
        return reference, low_lim, upp_lim
