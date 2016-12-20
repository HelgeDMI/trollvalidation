import numpy as np
from numpy import ma
import logging

LOG = logging.getLogger(__name__)

"""
according to https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid

Ice Concentration from Egg Code 	SIGRID Code 	EASE-Grid Product Value for Concentration
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
"""

class DecodeSIGRIDCodes(object):
    def decode_values(self, data_eval, product_file_data):
        try:
            sigrid_codes = self.bin_intervals_to_sigrid_codes(data_eval)
            LOG.debug('Converted bin intervals to sigrid codes')
        except ValueError:
            sigrid_codes = data_eval
            LOG.debug('Trying to decode assuming sigrid codes...')

        decoded_ice_conc = self.sigrid_decoding(sigrid_codes, product_file_data)
        return decoded_ice_conc

    def bin_intervals_to_sigrid_codes(self, data_eval):
        """
        For documentation on the bin files:
        https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid/#format
        """

        data_eval = data_eval.astype(int)

        expected_vals = [0, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 100]
        for v in np.unique(data_eval):
            if (not v in expected_vals) and (not isinstance(v, np.ma.core.MaskedConstant)):
                LOG.debug('Not a bin file as contains {0}'.format(v))
                raise ValueError

        codes = np.zeros(data_eval.shape)
        codes.fill(np.nan)
        codes[data_eval == 0] = 0
        codes[data_eval == 5] = 1
        codes[data_eval == 10] = 2  # TODO: Check this
        codes[data_eval == 20] = 13
        codes[data_eval == 30] = 24
        codes[data_eval == 40] = 35
        codes[data_eval == 50] = 46
        codes[data_eval == 60] = 57
        codes[data_eval == 70] = 68
        codes[data_eval == 80] = 79
        codes[data_eval == 90] = 81
        codes[data_eval == 95] = 91
        codes[data_eval == 100] = 92
        codes = ma.masked_invalid(codes)
        return codes

    def sigrid_decoding(self, data_eval, data_orig):
        data_eval = data_eval.astype(int)

        expected_vals = [0, 1, 2, 13, 24, 35, 46, 57, 68, 79, 81, 91, 92, 99]
        for v in np.unique(data_eval):
            if (not v in expected_vals) and (not isinstance(v, np.ma.core.MaskedConstant)):
                raise ValueError('Skipping this file: value {0} was not expected in sigrid code'.format(v))

        de = data_eval
        condition_choice = np.array([
            (de == 00,   0,  0),
            (de == 01,   0, 10),  # TODO: Check this
            (de == 02,   0, 20),  # TODO: Check this
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
            (de == 99, np.nan, np.nan)
        ])
        cond, lower_limit, upper_limit = condition_choice.T
        lower_limits = np.select(cond, lower_limit)
        upper_limits = np.select(cond, upper_limit)

        do = data_orig
        condition = [(do >= lower_limits) & (do <= upper_limits),
                     do < lower_limits,
                     do > upper_limits]
        choice = [do,
                  lower_limits,
                  upper_limits]
        reference = np.select(condition, choice, default=np.nan)

        if np.any(np.isnan(reference)):
            LOG.warning('Not all values decoded: contains NaNs')

        if isinstance(data_eval, np.ma.core.MaskedArray):
            reference = np.ma.array(reference, mask=(data_eval.mask | np.isnan(reference)))

        return reference

    #
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
