#!/usr/bin/env python

import sys
import os
import logging
import random
import string
import numpy as np
import multiprocessing as mp
import trollvalidation.validation_utils as util
import trollvalidation.validation_functions as val_func

from dateutil import rrule
from datetime import datetime, date, timedelta
from trollvalidation.validation_utils import TmpFiles
from trollvalidation.validation_decorators import timethis, around_step, \
    around_task, PreReturn
import configuration as cfg

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')

cfg.CSV_HEADER = ['reference_time', 'run_time', 'my_val']


def generate_time_series():
    # all in the following creates a time series mock up.
    days_back = 8
    start_date = datetime.today() - timedelta(days=days_back + 1)
    times = list(rrule.rrule(rrule.DAILY, count=days_back, dtstart=start_date))
    times_str = [datetime.strftime(t, '%Y-%m-%d') for t in times]
    eval_paths = [datetime.strftime(t, '/tmp/eval%d') for t in times]
    orig_paths = [datetime.strftime(t, '/tmp/orig%d') for t in times]

    # the only important thing is that a pre validation function returns a
    # data structure with a timestamp in the first column, a url to the
    # evaluation files in the second column, and a url to the original files
    # in the third column
    return zip(times_str, eval_paths, orig_paths)


def pre_func(ref_time, eval_file, orig_file):
    temp_files = TmpFiles()

    def prepare_orig_data():
        orig_data = np.array([1, 2, 3, 4])
        return orig_data

    def prepare_eval_data():
        eval_data = np.array([1, 2, 3, 4])
        return eval_data

    return PreReturn(temp_files, prepare_eval_data(), prepare_orig_data())


def val_step_star(input_tuple):
    return val_step(*input_tuple)


@timethis
@around_step(pre_func=pre_func, post_func=util.cleanup)
def val_step(ref_time, data_eval, data_orig):
    run_time = datetime.now().strftime('%Y-%m-%d %H:%m:%S')
    # TODO: implement your validation function in or choose one of
    # validation_functions.py
    # val_value = val_func.my_func(data_eval, data_orig)
    val_value = data_eval - data_orig

    return [ref_time, run_time, val_value]


@around_task(pre_func=generate_time_series, post_func=util.write_to_csv)
def val_task(file_pairs, description='', description_str=''):
    LOG.info(description)
    LOG.info(description_str)

    pool = mp.Pool(processes=mp.cpu_count())
    results = pool.map(val_step_star, file_pairs)
    pool.close()

    return results


if __name__ == '__main__':
    desc = 'An example validation task'
    desc_str = 'example_validation_{0}'.format(date.today())
    val_task(description=desc, description_str=desc_str)
