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
