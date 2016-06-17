import numpy as np
import pyresample as pr
import trollvalidation.validation_utils as util


class BINFileReader(object):

    def __init__(self):
        self.data = None

    def _read_bin_file(self, fname):
        """
        This function reads the binary NIC ice chart received from:
        ftp://sidads.colorado.edu/pub/DATASETS/NOAA/G02172/weekly

        According to the documentation:
        https://nsidc.org/data/docs/noaa/g02172_nic_charts_climo_grid/#format

        # Value 	Description
        # 0 - 100 	Ice concentration (percent) or frequency of occurrence
        #           (percent) (in multiples of 5)
        # 108 	Fast ice
        # 157 	Undigitized (appears in some early charts)
        # 253 	Areas not covered
        # 254 	Land

        The ice concentration is given by values in between [0..100],
        where 0 means water and the other values, multiples of 5, denote
        ice concentration in percent. Consequently, this reader masks out
        all other values, i.e. values larger than 100.

        The binary file contains 361*361 bytes holding the information
        described above.

        The ice chart is resampled to the area definiton of the ice
        concentration product to which it is compared.

        :param fname: str
            Path to a binary NIC ice chart.

        :param product_file: str
            Path to a binary NIC ice chart.

        :return: np.ma.array
            A two-dimensional array, which holds the resampled ice
            concentrations of a NIC ice chart.
        """

        self.data = np.fromfile(fname, dtype=np.uint8).reshape(361, 361)
        self.data = self.data.astype(np.float32)

        return self.data

    def _reproject(self, input_file, product_file):

        target_area_def = util.get_area_def(product_file)
        source_area_def = util.get_area_def(input_file)

        data = np.ma.array(self.data, mask=(self.data > 100))
        data_con_nn = pr.image.ImageContainerNearest(data, source_area_def,
                                                     radius_of_influence=50000)

        result = data_con_nn.resample(target_area_def)

        return result.image_data

    def read_data(self, input_file, product_file):
        _ = self._read_bin_file(input_file)
        return self._reproject(input_file, product_file)
