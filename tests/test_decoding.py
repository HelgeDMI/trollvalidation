import pytest
import numpy as np
from trollvalidation.data_decoders.sigrid_decoder import DecodeSIGRIDCodes



@pytest.fixture(scope='module')
def setup_decoding():
    sigrid_decoder = DecodeSIGRIDCodes()
    return sigrid_decoder

def test_sigrid_decoding(setup_decoding):
    data_eval = np.array([[13, 24, 91, 91],
                          [00, 01, 01, 35],
                          [68, 46, 92, 79],
                          [68, 92, 91, 81]])
    data_orig = np.array([[20,  8, 100, 100],
                          [86, 30, 5, 50],
                          [23,  5, 22, 60],
                          [61, 80, 10, 60]])
    data_expe = np.array([[20, 20, 100, 100],
                          [0,  10,  5, 50],
                          [60, 40, 100, 70],
                          [61,100, 90, 80]])

    # do decoding
    decoded_data = setup_decoding.sigrid_decoding(data_eval, data_orig)

    print(decoded_data - data_expe)
    assert np.array_equal(data_expe, decoded_data)

