import numpy as np


class DecodeSIGRIDCodes(object):
    def decode_values(self, data_eval, product_file_data):
        if data_eval[(data_eval > 10) & (data_eval < 90) & \
                (data_eval % 10 == 5)].any():
            print('File seems to contain ice concentrations in 5\% steps...')
            print(data_eval[(data_eval > 10) & (data_eval < 90) & (data_eval
                                                                   % 10 == 5)])
            return data_eval
        else:
            ease_as_sigrid_codes = self.ease_codes_to_sigrid_codes(data_eval)
            decoded_ice_conc = self.sigrid_decoding(ease_as_sigrid_codes,
                                                    product_file_data)
            return decoded_ice_conc

    def ease_codes_to_sigrid_codes(self, data_eval):
        data_eval[data_eval == 5] = 1
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
