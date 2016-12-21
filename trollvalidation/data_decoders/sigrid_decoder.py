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

"""

LOG = logging.getLogger(__name__)


class DecodeSIGRIDCodes(object):

    @staticmethod
    def valid_values_check(data_eval, expected):
        for v in np.unique(data_eval):
            if (not v in expected) and (not isinstance(v, np.ma.core.MaskedConstant)):
                    raise ValueError('Unexpected value in file: {0}'.format(v))

    def intervals_to_sigrid_codes(self, data_eval):
        """
        Convert the bin intervals to the corresponding sigrid codes
        For documentation on the bin files:
        https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid/#format
        """
        expected = [0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100, 99]
        self.valid_values_check(data_eval, expected)
        de = data_eval
        # condition_choices is [(de == concentration_interval, sigrid_code), ...]
        condition_choice = [
            (de == 05,  01),  # TODO: Check this. It can also be 2.
            (de == 95,  91),
            (de == 100, 92),
            (de == 99, 255)
        ]
        condition, choice = zip(*condition_choice)
        codes = np.select(condition, choice, default=de)

        if isinstance(de, np.ma.core.MaskedArray):
            codes = np.ma.array(codes, mask=de.mask)

        return codes

    def sigrid_decoding(self, data_eval, data_orig):
        data_eval = data_eval.astype(int)

        # Check that there are no unexpected values

        expected = [00, 01, 02, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25,
                    26, 27, 28, 29, 30, 31, 34, 35, 36, 37, 38, 39, 40, 41, 45, 46, 47, 48,
                    49, 50, 51, 56, 57, 58, 59, 60, 61, 67, 68, 69, 70, 71, 78, 79, 80, 81,
                    89, 90, 91, 92, 255]
        self.valid_values_check(data_eval, expected)

        # Convert the sigrid codes to upper and lower limits of ice concentration

        de = data_eval
        cl = 10 * (de // 10)  # lower code: 1st digit * 10
        cu = 10 * (de % 10)   # upper code: 2nd digit * 10
        condition_choices = [
            (de == 255, np.nan, np.nan),
            (de == 00, 0,  0),
            (de == 01, 0, 10),
            (de == 02, 0, 10),  # TODO: Check this
            (de == 92, 100, 100),
            (cu == 10, cl, 100),        # 21, 31, 41, 51, 61, 71, 81, 91
            (cu == 00, de, de),         # 10, 20, 30, 40, 50, 60, 70, 80, 90
            (~(de % 10 == 0), cl, cu)   # 12, 13, 14, 15, 16, 17, 18, 19, 23, 24, 25,
                                        # 26, 27, 28, 29, 34, 35, 36, 37, 38, 39, 45,
                                        # 46, 47, 48, 49, 56, 57, 58, 59, 67, 68, 69,
                                        # 78, 79, 89
        ]
        condition, lower_limit, upper_limit = zip(*condition_choices)
        lower_limits = np.select(condition, lower_limit, default=-128)
        upper_limits = np.select(condition, upper_limit, default=-128)

        if (-128 in lower_limits) or (-128 in upper_limits):
            raise ValueError('Values {} not decoded'.format(de[(lower_limits == -128) | (upper_limits == -128)]))

        try:
            assert np.any((upper_limits >= lower_limits) | np.isnan(upper_limits) | np.isnan(lower_limits))
        except:
            u, l = upper_limit[upper_limits < lower_limits], lower_limits[upper_limits < lower_limits]
            raise ValueError('Sigrid decoding invalid: {0} (upper) < {1} (lower)'.format(u, l))

        # The variable 'reference' is the closet possible value of the NIC data to data_orig, given that the NIC data
        # can be an interval. So, if the NIC sigrid codes specify limit, they converted to a reference as follows:
        #   * if data_orig is within the bounds of the NIC limits, reference = data_orig
        #   * otherwise, reference is equal to the closest limit of the NIC interval.
        # If the NIC codes are specific values, rather that limits, 'reference' is equal to data_eval

        do, ll, ul = data_orig, lower_limits, upper_limits
        # 'condition_choice' is a follows: [(interval, choice),...]
        condition_choice = [((do >= ll) & (do <= ul), do),
                            (do < ll,                 ll),
                            (do > ul,                 ul)]
        cond, choice = zip(*condition_choice)
        reference = np.select(cond, choice, default=de)

        if np.any(np.isnan(reference)):
            LOG.info('The file contains undetermined values')

        if isinstance(data_eval, np.ma.core.MaskedArray):
            reference = ma.array(reference, mask=(data_eval.mask | np.isnan(reference)))

        return reference

    def easegrid_decoding(self, data_eval, product_file_data):
        data_eval = data_eval.astype(int)
        sigrid_codes = self.intervals_to_sigrid_codes(data_eval)
        reference = self.sigrid_decoding(sigrid_codes, product_file_data)
        return reference

    # def sigrid_decoding(self, data_eval, data_orig):
    #     """
    #     Decodes a
    #     SIGRID ice codes: http://www.natice.noaa.gov/products/sigrid.html
    #     :param data_eval: np.array|np.ma.array
    #         An array holding SIGRID ice concentration codes,
    #         which originate from a shapefile or a sig file
    #     :param data_orig: np.array|np.ma.array
    #         An array holding ice concentration values in the range 0 .. 100
    #         in one percent steps. 0 means open water and 100 is the highest
    #         possible ice concentration.
    #     :return: np.array|np.ma.array
    #         Returns a modified version of data_eval, where all numbers
    #         are replaced according to the following rules:
    #
    #         0..9                ->  0
    #         92                  ->  100
    #         (?P<fst>\d{1})1     ->  fst0,           if val(data_orig) < fst0
    #                                 100,            if val(data_orig) > 100
    #                                 val(data_orig)  if fst0 <= val(data_orig) <= 100
    #         (?P<fst>\d{1})(?P<snd>\d{1})
    #                             ->  fst0,           if val(data_orig) < fst0
    #                                 100,            if val(data_orig) > snd0
    #                                 val(data_orig)  if fst0 <= val(data_orig) <= snd0
    #     """
    #     # We think there should not be any values like 51, 52, 53, 54, 55
    #     # If this one is hit we have to talk about the SIGRID code conversion
    #     # again
    #     # undesired_values = data_eval[(data_eval % 10 != 1) & (data_eval != 92) &
    #     #                    (data_eval % 10 != 0) &
    #     #                    (data_eval / 10 >= data_eval % 10)]
    #     # if not undesired_values == []:
    #     #     assert data_eval[(data_eval % 10 != 1) & (data_eval != 92) &
    #     #                      (data_eval % 10 != 0) &
    #     #                      (data_eval / 10 >= data_eval % 10)].any() == False
    #
    #     LOG.debug('data_eval unique values {}'.format(np.unique(data_eval)))
    #
    #     expected_vals = [0.0, 1.0, 2.0, 13.0, 24.0, 35.0, 46.0, 57.0, 68.0, 79.0, 81.0, 91.0, 92.0, 99.0]
    #     vals = np.unique(data_eval)
    #     for v in vals:
    #         if (not v in expected_vals) and (not isinstance(v, np.ma.core.MaskedConstant)):
    #             raise ValueError('Value {0} was not expected in sigrid code'.format(v))
    #
    #     was_masked = False
    #     if isinstance(data_eval, np.ma.core.MaskedArray):
    #         mask = data_eval.mask
    #         was_masked = True
    #
    #     # set water to 0
    #     condition = (data_eval < 9)
    #     processed = condition
    #     data_eval[condition] = 0
    #
    #     # set 92 to 100
    #     condition = (processed != True) & (data_eval == 92)
    #     processed = processed | condition
    #     data_eval[condition] = 100
    #
    #     # handle 21, 31, 41, 51, 61, 71, 81, 91
    #     condition = (processed != True) & (data_eval % 10 == 1) & \
    #                 (data_orig == 100)
    #     processed = processed | condition
    #     data_eval = np.where(condition, 100, data_eval)
    #
    #     condition = (processed != True) & (data_eval % 10 == 1) & \
    #                 (data_orig < (data_eval / 10) * 10)
    #     processed = processed | condition
    #     data_eval = np.where(condition, (data_eval / 10) * 10, data_eval)
    #
    #     condition = (processed != True) & (data_eval % 10 == 1) & \
    #                 (data_orig >= (data_eval / 10) * 10) & (data_orig < 100)
    #     processed = processed | condition
    #     data_eval = np.where(condition, data_orig, data_eval)
    #
    #     condition = (data_eval == 91) & (data_orig < 90)
    #     processed = processed | condition
    #     data_eval = np.where(condition, 90, data_eval)
    #
    #     condition = (data_eval == 91) & (data_orig >= 90) & (data_orig <= 100)
    #     processed = processed | condition
    #     data_eval = np.where(condition, data_orig, data_eval)
    #
    #     # handle other intervals, i.e., SIGRID codes such as 34, 46,
    #     condition = (processed != True) & (data_eval % 10 != 0) & \
    #                 (data_orig > (data_eval % 10) * 10)
    #     processed = processed | condition
    #     data_eval = np.where(condition, (data_eval % 10) * 10, data_eval)
    #
    #     condition = (processed != True) & (data_eval % 10 != 0) & \
    #                 (data_orig < (data_eval / 10) * 10)
    #     processed = processed | condition
    #     data_eval = np.where(condition, (data_eval / 10) * 10, data_eval)
    #
    #     condition = (processed != True) & (data_eval % 10 != 0) & \
    #                 (data_orig >= (data_eval / 10) * 10) & \
    #                 (data_orig <= (data_eval % 10) * 10)
    #     data_eval = np.where(condition, data_orig, data_eval)
    #
    #
    #     if was_masked:
    #         data_eval = np.ma.array(data_eval, mask=mask)
    #
    #     return data_eval
