import numpy as np
import logging

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')

class DecodeSIGRIDCodes(object):
    # def decode_values(self, data_eval, product_file_data):
    #     if data_eval[(data_eval > 10) & (data_eval < 90) & \
    #             (data_eval % 10 == 5)].any():
    #         print('File seems to contain ice concentrations in 5\% steps...')
    #         print(data_eval[(data_eval > 10) & (data_eval < 90) & (data_eval
    #                                                                % 10 == 5)])
    #         return data_eval
    #     else:
    #         ease_as_sigrid_codes = self.ease_codes_to_sigrid_codes(data_eval)
    #         decoded_ice_conc = self.sigrid_decoding(ease_as_sigrid_codes,
    #                                                 product_file_data)
    #         return decoded_ice_conc

    def decode_values(self, data_eval, product_file_data):
        ease_as_sigrid_codes = self.ease_codes_to_sigrid_codes(data_eval)
        decoded_ice_conc = self.sigrid_decoding(ease_as_sigrid_codes,
                                                product_file_data)
        return decoded_ice_conc

    # def decode_values(self, data_eval, product_file_data):
    #     if data_eval[(data_eval > 10) & (data_eval < 90) & \
    #             (data_eval % 10 == 5)].any():
    #         LOG.info('File contains ice concentrations in 5% steps: {0}'.format(np.unique(data_eval)))
    #     else:
    #         LOG.info('File contains ice concentrations in these steps {0}'.format(np.unique(data_eval)))
    #     ease_as_sigrid_codes = self.ease_codes_to_sigrid_codes(data_eval)
    #     decoded_ice_conc = self.sigrid_decoding(ease_as_sigrid_codes,
    #                                             product_file_data)
    #     return decoded_ice_conc


    # def ease_codes_to_sigrid_codes(self, data_eval):
    #     data_eval[data_eval == 5] = 1
    #     data_eval[data_eval == 95] = 91
    #     data_eval[data_eval == 100] = 92
    #     return data_eval

    def ease_codes_to_sigrid_codes(self, data_eval):
        expected_vals = [0.0, 5.0, 15.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 95.0, 100.0, np.ma.core.MaskedConstant]
        vals = np.unique(data_eval)
        for v in vals:
            if (not v in expected_vals) and (not isinstance(v, np.ma.core.MaskedConstant)):
                raise ValueError('Value {0} was not expected'.format(v))

        data_eval[data_eval == 5] = 1
        data_eval[data_eval == 15] = 2  # TODO: This is just a guess
        data_eval[data_eval == 20] = 13
        data_eval[data_eval == 20] = 13
        data_eval[data_eval == 30] = 24
        data_eval[data_eval == 40] = 35
        data_eval[data_eval == 50] = 46
        data_eval[data_eval == 60] = 57
        data_eval[data_eval == 70] = 68
        data_eval[data_eval == 80] = 79
        data_eval[data_eval == 90] = 81
        data_eval[data_eval == 95] = 91
        data_eval[data_eval == 100] = 92
        return data_eval

    def sigrid_decoding(self, data_eval, data_orig):
        """
        Decodes a
        SIGRID ice codes: http://www.natice.noaa.gov/products/sigrid.html
        :param data_eval: np.array|np.ma.array
            An array holding SIGRID ice concentration codes,
            which originate from a shapefile or a sig file
        :param data_orig: np.array|np.ma.array
            An array holding ice concentration values in the range 0 .. 100
            in one percent steps. 0 means open water and 100 is the highest
            possible ice concentration.
        :return: np.array|np.ma.array
            Returns a modified version of data_eval, where all numbers
            are replaced according to the following rules:

            0..9                ->  0
            92                  ->  100
            (?P<fst>\d{1})1     ->  fst0,           if val(data_orig) < fst0
                                    100,            if val(data_orig) > 100
                                    val(data_orig)  if fst0 <= val(data_orig) <= 100
            (?P<fst>\d{1})(?P<snd>\d{1})
                                ->  fst0,           if val(data_orig) < fst0
                                    100,            if val(data_orig) > snd0
                                    val(data_orig)  if fst0 <= val(data_orig) <= snd0
        """
        # We think there should not be any values like 51, 52, 53, 54, 55
        # If this one is hit we have to talk about the SIGRID code conversion
        # again
        # undesired_values = data_eval[(data_eval % 10 != 1) & (data_eval != 92) &
        #                    (data_eval % 10 != 0) &
        #                    (data_eval / 10 >= data_eval % 10)]
        # if not undesired_values == []:
        #     assert data_eval[(data_eval % 10 != 1) & (data_eval != 92) &
        #                      (data_eval % 10 != 0) &
        #                      (data_eval / 10 >= data_eval % 10)].any() == False

        LOG.debug('data_eval unique values {}'.format(np.unique(data_eval)))

        was_masked = False
        if isinstance(data_eval, np.ma.core.MaskedArray):
            mask = data_eval.mask
            was_masked = True

        # set water to 0
        condition = (data_eval < 9)
        processed = condition
        data_eval[condition] = 0

        # set 92 to 100
        condition = (processed != True) & (data_eval == 92)
        processed = processed | condition
        data_eval[condition] = 100

        # handle 21, 31, 41, 51, 61, 71, 81, 91
        condition = (processed != True) & (data_eval % 10 == 1) & \
                    (data_orig == 100)
        processed = processed | condition
        data_eval = np.where(condition, 100, data_eval)

        condition = (processed != True) & (data_eval % 10 == 1) & \
                    (data_orig < (data_eval / 10) * 10)
        processed = processed | condition
        data_eval = np.where(condition, (data_eval / 10) * 10, data_eval)

        condition = (processed != True) & (data_eval % 10 == 1) & \
                    (data_orig >= (data_eval / 10) * 10) & (data_orig < 100)
        processed = processed | condition
        data_eval = np.where(condition, data_orig, data_eval)

        condition = (data_eval == 91) & (data_orig < 90)
        processed = processed | condition
        data_eval = np.where(condition, 90, data_eval)

        condition = (data_eval == 91) & (data_orig >= 90) & (data_orig <= 100)
        processed = processed | condition
        data_eval = np.where(condition, data_orig, data_eval)

        # handle other intervals, i.e., SIGRID codes such as 34, 46,
        condition = (processed != True) & (data_eval % 10 != 0) & \
                    (data_orig > (data_eval % 10) * 10)
        processed = processed | condition
        data_eval = np.where(condition, (data_eval % 10) * 10, data_eval)

        condition = (processed != True) & (data_eval % 10 != 0) & \
                    (data_orig < (data_eval / 10) * 10)
        processed = processed | condition
        data_eval = np.where(condition, (data_eval / 10) * 10, data_eval)

        condition = (processed != True) & (data_eval % 10 != 0) & \
                    (data_orig >= (data_eval / 10) * 10) & \
                    (data_orig <= (data_eval % 10) * 10)
        data_eval = np.where(condition, data_orig, data_eval)


        if was_masked:
            data_eval = np.ma.array(data_eval, mask=mask)

        return data_eval
