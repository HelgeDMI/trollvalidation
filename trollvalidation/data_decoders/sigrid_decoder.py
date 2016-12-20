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

Undetermined                            99                      255 # Assuming 255 in undetermined,
                                                                    # but not verified

Concentration Intervals
(Cl = lowest concentration in interval
(Ch = highest concentration in interval)	ClCh
Examples:
1/10 - 3/10	                            13	                    20
4/10 - 6/10	                            46	                    50
7/10 - 9/10	                            79	                    80
7/10 - 10/10	                        71                  	85 # How does this follow?

Table 9.

EASE-Grid Climatology Data File Values:
Ice concentration (percent) or frequency of occurrence (percent) (in multiples of 5)

## Description of EASE Grid Format
https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid/#format

## Description of GRIDDED SIGRID FORMAT FOR SEA ICE
http://www.natice.noaa.gov/products/sigrid.html

The sigrid and sig files appear to sometimes have a mixture of sigrid codes and ice concentration intervals.

***
The bin files sometimes also contain value 15. I cannot find this code in the documentation,
so it is not clear what the sigrid code should be.
***

"""

LOG = logging.getLogger(__name__)


class DecodeSIGRIDCodes(object):

    def decode_values(self, data_eval, product_file_data):
        data_eval = data_eval.astype(int)
        self.valid_values_check(data_eval)
        sigrid_codes = self.intervals_to_sigrid_codes(data_eval)
        reference = self.sigrid_decoding(sigrid_codes, product_file_data)
        return reference

    @staticmethod
    def valid_values_check(data_eval):
        expected_intervals = [0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100, 99]
        expected_sigrid = [0, 1, 2, 13, 24, 35, 46, 57, 68, 79, 81, 91, 92, 255]
        expected = expected_intervals + expected_sigrid
        for v in np.unique(data_eval):
            if (not v in expected) and (not isinstance(v, np.ma.core.MaskedConstant)):
                if v == 15:
                    LOG.warning('I do not know what to do with a value of 15')
                else:
                    raise ValueError('Unexpected value in file: {0}'.format(v))

    @staticmethod
    def intervals_to_sigrid_codes(data_eval):
        """
        Convert the bin intervals to the corresponding sigrid codes
        For documentation on the bin files:
        https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid/#format
        """
        de = data_eval
        # condition_choices is [(de == concentration_interval, sigrid_code), ...]
        condition_choice = [
            (de == 0,    0),
            (de == 5,    1),   # TODO: Check this. It can also be 2.
            (de == 10,   2),   # TODO: Check this.
            (de == 15,  255),  # TODO: This is wrong! What should it be?
            (de == 20,  13),
            (de == 30,  24),
            (de == 40,  35),
            (de == 50,  46),
            (de == 60,  57),
            (de == 70,  68),
            (de == 80,  79),
            (de == 90,  81),
            (de == 95,  91),
            (de == 100, 92),
            (de == 99, 255)
        ]
        condition, choice = zip(*condition_choice)
        codes = np.select(condition, choice, default=de)

        if isinstance(de, np.ma.core.MaskedArray):
            codes = np.ma.array(codes, mask=de.mask)

        return codes

    @staticmethod
    def sigrid_decoding(data_eval, data_orig):

        # Check that there are no unexpected values

        expected_vals = [0, 1, 2, 13, 24, 35, 46, 57, 68, 79, 81, 91, 92, 255]
        # Sometimes I also get 10, 20
        for v in np.unique(data_eval):
            if (not v in expected_vals) and (not isinstance(v, np.ma.core.MaskedConstant)):
                raise ValueError('Skipping this file: value {0} was not expected in sigrid code'.format(v))

        # Convert the sigrid codes to upper and lower limits of ice concentration

        de = data_eval
        # condition_choices is [(de == sigrid_code, lower_limit, upper_limit), ...]
        condition_choices = [
            (de == 00,   0,  0),
            (de == 01,   0, 10),
            (de == 02,   0, 10),  # TODO: Check this
            (de == 13,  10, 30),
            (de == 24,  20, 40),
            (de == 35,  30, 50),
            (de == 46,  40, 60),
            (de == 57,  50, 70),
            (de == 68,  60, 80),
            (de == 79,  70, 90),
            (de == 81,  80, 100),
            (de == 91,  90, 100),
            (de == 92, 100, 100),
            (de == 255, np.nan, np.nan)
        ]
        condition, lower_limit, upper_limit = zip(*condition_choices)
        lower_limits = np.select(condition, lower_limit)
        upper_limits = np.select(condition, upper_limit)

        # The variable reference is the closet value of data_orig to NIC data, given that the NIC
        # data is an interval. So, the NIC sigrid codes are converted to a reference as follows:
        # * if data_orig is within the bounds of the NIC limits, reference = data_orig
        # * otherwise, reference is equal to the closest limit of the NIC interval

        do, ll, ul = data_orig, lower_limits, upper_limits
        # condition_choice is a follows: [(interval, choice),...]
        condition_choice = [((do >= ll) & (do <= ul), do),
                            (do < ll,                 ll),
                            (do > ul,                 ul)]
        cond, choice = zip(*condition_choice)
        reference = np.select(cond, choice, default=de)

        if np.any(np.isnan(reference)):
            LOG.info('The file contains undetermined values')

        if isinstance(data_eval, np.ma.core.MaskedArray):
            reference = np.ma.array(reference, mask=(data_eval.mask | np.isnan(reference)))

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
