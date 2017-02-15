import numpy as np
import pyresample as pr
import trollvalidation.validation_utils as util


class SIGFileReader(object):
    """
    This decoder is built relying on the information given in:
    http://nsidc.org/pubs/documents/special/nsidc_special_report_13.pdf
    pp. 33

    :param fname: str
        A path to a sigrid code file as it can be downloaded from:
        http://wdc.aari.ru/datasets/d0001/south/nic/

    :return: np.array
    """

    def __init__(self):
        self.ice_codes = None
        self.lats = None
        self.lons = None

    def _read_sig_file(self, fname):
        """
        This decoder is built relying on the information given in:
        http://nsidc.org/pubs/documents/special/nsidc_special_report_13.pdf
        pp. 33

        :param fname: str
            A path to a sigrid code file as it can be downloaded from:
            http://wdc.aari.ru/datasets/d0001/south/nic/

        :return: np.array
        """

        # open the file and read it as text
        with open(fname) as f:
            # use splitlines to get rid of trailing \r\n
            content = f.read().splitlines()

        # concatenate the lines of text to blocks of information
        blocks = []
        for idx, line in enumerate(content):
            if idx == 0:
                # get the ice chart's resolution out of the header
                y_res = int(line.split(':')[4].replace('B', '')[0:3])
                x_res = int(line.split(':')[4].replace('B', '')[3:7])
            if idx == 1:
                # header lines, currently I skip them
                # they are needed to compute lat and lon values
                pass
            if idx == len(content) - 1:
                # last line take it out...
                # it contains ':99:99:99' and I do not know what it means,
                # except to mark the end of the file
                pass

            if line.startswith('=K'):
                # block with data starts with its own header
                new_block = []
                number_of_lines = int(line.split(':')[3].replace('X', ''))

                for data_line_idx in range(idx + 1, idx + 1 + number_of_lines):
                    new_block.append(content[data_line_idx])

                joined_str = ''.join(new_block)
                wo_leading_colon = joined_str[1:len(joined_str)]
                rolls_splitted = wo_leading_colon.split(':')
                blocks.append((line, rolls_splitted))

        # convert the text to a matrix holding the ice concentration codes

        # location information as given in the documentation
        # http://wdc.aari.ru/datasets/d0001/south/nic/ pp.34
        line_lat_min = -50.0
        line_lat_max = -85.0
        line_lon_min = -180.0
        line_lon_max = 180.0
        deg_between_lines = 0.25

        icechart_data = np.array([])
        lats = np.array([])
        lons = np.array([])

        for header, block in blocks:
            line_number = int(header.split(':')[1].replace('L', '')[0:3])
            line_length = int(header.split(':')[2].replace('M', ''))

            # create the latitude values for this line
            line_lats = np.zeros(x_res)
            current_lat = line_lat_min - (deg_between_lines * (line_number - 1))
            line_lats.fill(current_lat)
            lats = np.append(lats, line_lats)

            # create the longitude values for this line
            line_lons = np.arange(line_lon_min, line_lon_max, 360.0 /
                                  line_length)
            if x_res > line_length:
                # stretch the line to fill the entire length
                line_lons = np.repeat(line_lons, (x_res / line_length))
            lons = np.append(lons, line_lons)

            # read the ice concentration codes for this line
            line_icecode = np.array([])
            for roll in block:
                roll_len = int(roll[1:3])

                for idx in range(0, roll_len):
                    if roll[3:5] == 'LL':
                        # set land
                        line_icecode = np.append(line_icecode, 255)
                    elif roll[3:5] == 'CT':
                        # set ice conc code
                        line_icecode = np.append(line_icecode, int(roll[5:7]))
                    else:
                        msg = 'I do not know how to decode {0}'
                        raise Exception(msg.format(roll[3:5]))
            assert len(line_icecode) == line_length

            if x_res > line_length:
                # stretch the line to fill the entire length
                line_icecode = np.repeat(line_icecode, x_res / line_length)
            icechart_data = np.append(icechart_data, line_icecode)

        icechart_data = icechart_data.reshape(icechart_data.shape[0] / x_res,
                                              x_res)
        lats = lats.reshape(lats.shape[0] / x_res, x_res)
        lons = lons.reshape(lons.shape[0] / x_res, x_res)

        self.ice_codes = icechart_data
        self.lats = lats
        self.lons = lons
        return icechart_data, lats, lons

    def _reproject(self, input_file, product_file):

        target_area_def = util.get_area_def(product_file)

        swath_def = pr.geometry.SwathDefinition(lons=self.lons, lats=self.lats)
        swath_con = pr.image.ImageContainerNearest(self.ice_codes, swath_def,
                                                   radius_of_influence=50000)
        area_con = swath_con.resample(target_area_def)
        reprojected_data = area_con.image_data

        return reprojected_data, self.lats, self.lons

    def read_data(self, input_file, product_file):
        _ = self._read_sig_file(input_file)
        return self._reproject(input_file, product_file)
