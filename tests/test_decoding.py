import pytest
import numpy as np
from trollvalidation.data_decoders.sigrid_decoder import DecodeSIGRIDCodes



@pytest.fixture(scope='module')
def setup_decoding():
    sigrid_decoder = DecodeSIGRIDCodes()
    return sigrid_decoder


def test_sigrid_decoding(setup_decoding):
    data_ref = np.array([[00, 00, 01, 02, 10, 11],
                          [12, 13, 14, 15, 16, 17],
                          [18, 19, 20, 21, 23, 24],
                          [25, 26, 27, 28, 29, 30],
                          [31, 34, 35, 36, 37, 38],
                          [39, 40, 41, 45, 46, 47],
                          [48, 49, 50, 51, 56, 57],
                          [58, 59, 60, 61, 67, 68],
                          [69, 70, 71, 78, 79, 80],
                          [81, 89, 90, 91, 92, 92]])

    data_test = np.array([[33, 85,  4, 92, 77, 44],
                          [76, 18, 88, 18, 44, 32],
                          [12, 68, 34, 37, 56,  4],
                          [51, 61, 77,  7, 95, 98],
                          [57, 26,  5, 17, 35, 72],
                          [54, 66, 68,  9, 60, 45],
                          [74, 24,  2, 93, 98, 69],
                          [07, 78, 79, 77, 43, 43],
                          [14, 18, 28, 37, 85,  8],
                          [29, 19, 40,  6, 36, 36]])

    data_expe = np.array([[00, 00,  4, 10, 10, 44],
                          [20, 18, 40, 18, 44, 32],
                          [12, 68, 20, 37, 30, 20],
                          [50, 60, 70, 20, 90, 30],
                          [57, 30, 30, 30, 35, 72],
                          [54, 40, 68, 40, 60, 45],
                          [74, 40, 50, 93, 60, 69],
                          [50, 78, 60, 77, 60, 60],
                          [60, 70, 70, 70, 85, 80],
                          [80, 80, 90, 90, 100, 100]])

    decoded_data = setup_decoding.sigrid_decoding(data_ref, data_test)
    assert np.array_equal(data_expe, decoded_data)



def test_catch_error(setup_decoding):
    data_ref = np.array([[13, 24, 91, 91],
                          [00, 01, 01, 35],
                          [68, 65, 40, 79],
                          [68, 92, 91, 81]])
    # Value 65 is not valid and should give a ValueError
    data_test = np.array([[20, 8, 100, 100],
                          [86, 30, 5, 50],
                          [23, 5, 57, 60],
                          [61, 80, 10, 60]])

    try:
        setup_decoding.sigrid_decoding(data_ref, data_test)
    except ValueError:
        assert True
    else:
        assert False
