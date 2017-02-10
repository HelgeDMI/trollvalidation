"""
Validation functions.

Put here all those functions that you might compute in a validation step
"""

import numpy as np


def match_pct(data_ref, data_test, threshold):
    diff = np.abs(data_ref - data_test)
    div = float(np.sum(np.logical_and(diff >= 0, diff <= 100)))
    pct_within = 100 * np.sum(diff <= threshold) / div
    return pct_within


def total_bias(data_ref, data_test):
    diff = data_test - data_ref
    return diff.mean()


def total_std_dev(data_ref, data_test):
    diff = data_test - data_ref
    return diff.std()


def ice_bias(data_ref, data_test):
    only_ice_in_chart = np.ma.array(data_ref, mask=data_ref == 0)
    diff = data_test - only_ice_in_chart
    return diff.mean()


def ice_std_dev(data_ref, data_test):
    only_ice_in_chart = np.ma.array(data_ref, mask=data_ref == 0)
    diff = data_test - only_ice_in_chart
    return diff.std()


def water_bias(data_ref, data_test):
    only_water_in_chart = np.ma.array(data_ref, mask=data_ref > 0)
    diff = data_test - only_water_in_chart
    return diff.mean()


def water_std_dev(data_ref, data_test):
    only_water_in_chart = np.ma.array(data_ref, mask=data_ref > 0)
    diff = data_test - only_water_in_chart
    return diff.std()


def rmsdiff(data_ref, data_test):
    """
    This method computes the Root-Mean-Square (RMS) difference.
    The RMS denotes how similar two images are. The closer the value
    to zero, the more similar is the data hold in the two two-dimensional
    arrays.

    It is inspired by:
    http://code.activestate.com/recipes/577630-comparing-two-images/

    :param data_ref: np.array | np.ma.array
        A two dimensional array.
    :param data_test: np.array | np.ma.array
        A two dimensional array.
    :return: float
        The RMS difference, which is a float value.
    """
    assert data_ref.shape == data_test.shape

    diff = data_ref - data_test

    # the 101 comes from the value range 0..100
    h, _ = np.histogram(diff, bins=np.arange(101))
    sq = (value * (idx ** 2) for idx, value in enumerate(h))
    sum_of_squares = np.sum(sq)

    rms = np.sqrt(sum_of_squares / float(data_test.shape[0] *
                                         data_test.shape[1]))
    return rms


def ice_bias_for_high_in_eval(data_ref, data_test):
    mask_expr = ~((data_ref >= 90) * (data_ref <= 100))
    only_ice_in_chart = np.ma.array(data_ref, mask=mask_expr)
    diff = data_test - only_ice_in_chart
    return diff.mean()


def ice_std_dev_for_high_in_eval(data_ref, data_test):
    mask_expr = ~((data_ref >= 90) * (data_ref <= 100))
    only_ice_in_chart = np.ma.array(data_ref, mask=mask_expr)
    diff = data_test - only_ice_in_chart
    return diff.std()


def water_bias_for_low_in_eval(data_ref, data_test):
    mask_expr = ~((data_ref >= 0) * (data_ref < 10))
    only_water_in_chart = np.ma.array(data_ref, mask=mask_expr)
    diff = data_test - only_water_in_chart
    return diff.mean()


def water_std_dev_for_low_in_eval(data_ref, data_test):
    mask_expr = ~((data_ref >= 0) * (data_ref < 10))
    only_water_in_chart = np.ma.array(data_ref, mask=mask_expr)
    diff = data_test - only_water_in_chart
    return diff.std()


# def intermediate_bias(data_ref, data_test):
#     mask_expr = ~((data_ref >= 10) * (data_ref < 90))
#     intermediate_ice_in_chart = np.ma.array(data_ref, mask=mask_expr)
#     diff = data_test - intermediate_ice_in_chart
#     return diff.mean()
#
#
# def intermediate_std_dev(data_ref, data_test):
#     mask_expr = ~((data_ref >= 10) * (data_ref < 90))
#     intermediate_ice_in_chart = np.ma.array(data_ref, mask=mask_expr)
#     diff = data_test - intermediate_ice_in_chart
#     return diff.std()

def intermediate_bias(data_ref, data_test):
    mask_expr = ~((data_ref > 0) * (data_ref < 90))
    intermediate_ice_in_chart = np.ma.array(data_ref, mask=mask_expr)
    diff = data_test - intermediate_ice_in_chart
    return diff.mean()


def intermediate_std_dev(data_ref, data_test):
    mask_expr = ~((data_ref > 0) * (data_ref < 90))
    intermediate_ice_in_chart = np.ma.array(data_ref, mask=mask_expr)
    diff = data_test - intermediate_ice_in_chart
    return diff.std()

