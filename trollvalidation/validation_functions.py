"""
Validation functions.

Put here all those functions that you might compute in a validation step
"""

import numpy as np


def match_pct(data_eval, data_orig, threshold):
    diff = np.abs(data_eval - data_orig)
    div = float(np.sum(np.logical_and(diff >= 0, diff <= 100)))
    pct_within = 100 * np.sum(diff <= threshold) / div
    return pct_within


def total_bias(data_eval, data_orig):
    diff = data_orig - data_eval
    return diff.mean()


def total_std_dev(data_eval, data_orig):
    diff = data_orig - data_eval
    return diff.std()


def ice_bias(data_eval, data_orig):
    only_ice_in_chart = np.ma.array(data_eval, mask=data_eval == 0)
    diff = data_orig - only_ice_in_chart
    return diff.mean()


def ice_std_dev(data_eval, data_orig):
    only_ice_in_chart = np.ma.array(data_eval, mask=data_eval == 0)
    diff = data_orig - only_ice_in_chart
    return diff.std()


def water_bias(data_eval, data_orig):
    only_water_in_chart = np.ma.array(data_eval, mask=data_eval > 0)
    diff = data_orig - only_water_in_chart
    return diff.mean()


def water_std_dev(data_eval, data_orig):
    only_water_in_chart = np.ma.array(data_eval, mask=data_eval > 0)
    diff = data_orig - only_water_in_chart
    return diff.std()


def rmsdiff(data_eval, data_orig):
    """
    This method computes the Root-Mean-Square (RMS) difference.
    The RMS denotes how similar two images are. The closer the value
    to zero, the more similar is the data hold in the two two-dimensional
    arrays.

    It is inspired by:
    http://code.activestate.com/recipes/577630-comparing-two-images/

    :param data_eval: np.array | np.ma.array
        A two dimensional array.
    :param data_orig: np.array | np.ma.array
        A two dimensional array.
    :return: float
        The RMS difference, which is a float value.
    """
    assert data_eval.shape == data_orig.shape

    diff = data_eval - data_orig

    # the 101 comes from the value range 0..100
    h, _ = np.histogram(diff, bins=np.arange(101))
    sq = (value * (idx ** 2) for idx, value in enumerate(h))
    sum_of_squares = np.sum(sq)

    rms = np.sqrt(sum_of_squares / float(data_orig.shape[0] *
                                         data_orig.shape[1]))
    return rms

def ice_bias_for_high_in_eval(data_eval, data_orig):
    mask_expr = ~((data_eval >= 90) * (data_eval < 100))
    only_ice_in_chart = np.ma.array(data_eval, mask=mask_expr)
    diff = data_orig - only_ice_in_chart
    return diff.mean()


def ice_std_dev_for_high_in_eval(data_eval, data_orig):
    mask_expr = ~((data_eval >= 90) * (data_eval < 100))
    only_ice_in_chart = np.ma.array(data_eval, mask=mask_expr)
    diff = data_orig - only_ice_in_chart
    return diff.std()


def water_bias(data_eval, data_orig):
    mask_expr = ~((data_eval >= 0) * (data_evel < 10))
    only_water_in_chart = np.ma.array(data_eval, mask=mask_expr)
    diff = data_orig - only_water_in_chart
    return diff.mean()


def water_std_dev(data_eval, data_orig):
    mask_expr = ~((data_eval >= 0) * (data_evel < 10))
    only_water_in_chart = np.ma.array(data_eval, mask=mask_expr)
    diff = data_orig - only_water_in_chart
    return diff.std()


def intermediate_bias(data_eval, data_orig):
    mask_expr = ~((data_eval >= 10) * (data_evel < 90))
    intermediate_ice_in_chart = np.ma.array(data_eval, mask=mask_expr)
    diff = data_orig - intermediate_ice_in_chart
    return diff.mean()


def intermediate_std_dev(data_eval, data_orig):
    mask_expr = ~((data_eval >= 10) * (data_evel < 90))
    intermediate_ice_in_chart = np.ma.array(data_eval, mask=mask_expr)
    diff = data_orig - intermediate_ice_in_chart
    return diff.std()
