import datetime as dt
import json
import logging
import os
import re
from collections import OrderedDict

from data_collectors import downloader
from dateutil import parser

from trollvalidation.validations import configuration as cfg

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')


def extract_timestamp(from_string, with_r_pattern, with_date_pattern):
    # print(from_string, with_r_pattern, with_date_pattern)
    time_str = re.search(with_r_pattern, from_string).group()
    if '%W' in with_date_pattern:
        ref_date = dt.datetime.strptime(time_str + '-1', with_date_pattern +
                                        '-%w')
    else:
        ref_date = dt.datetime.strptime(time_str, with_date_pattern)
    # make common time
    timestamp = dt.datetime.strftime(ref_date, '%Y-%m-%d')
    return timestamp


def generate_osi450_product_timeseries(files):

    timeseries = OrderedDict()
    hemispheres = ['nh', 'sh']

    for h_str in hemispheres:
        prods = filter(lambda f: (h_str in f), files)

        regexp_date, date_pattern = cfg.METNO_DOWNL['remote_date_pattern']
        dates = [extract_timestamp(f, regexp_date, date_pattern) for f in prods]

        timeseries[h_str] = OrderedDict(zip(dates, prods))
    return timeseries


def generate_nic_bin_timeseries(files):
    timeseries = OrderedDict()
    hemispheres = ['nh']

    for h_str in hemispheres:

        regexp_date, date_pattern = cfg.NIC_BIN_DOWNL['remote_date_pattern']
        dates = [extract_timestamp(f, regexp_date, date_pattern) for f in files]

        timeseries[h_str] = OrderedDict(zip(dates, files))

    return timeseries


def generate_nic_sig_timeseries(files):
    timeseries = OrderedDict()
    hemispheres = ['sh']

    for h_str in hemispheres:

        regexp_date, date_pattern = cfg.NIC_SIG_DOWNL['remote_date_pattern']
        dates = [extract_timestamp(f, regexp_date, date_pattern) for f in files]

        timeseries[h_str] = OrderedDict(zip(dates, files))

    return timeseries


def generate_nic_shp_timeseries(files):
    timeseries = OrderedDict()
    hemispheres = [('nh', 'arctic'), ('sh', 'antarc')]
    for h_str, h_name in hemispheres:
        prods = filter(lambda f: (h_name in os.path.basename(f)), files)

        regexp_date, date_pattern = cfg.NIC_SHP_DOWNL['remote_date_pattern']
        dates = [extract_timestamp(f, regexp_date, date_pattern) for f in prods]

        timeseries[h_str] = OrderedDict(zip(dates, prods))

    return timeseries


def generate_nic_timeseries(shp_files, bin_files, sig_files):
    nic_files = {'nh': OrderedDict(bin_files['nh']),
                 'sh': OrderedDict(sig_files['sh'])}

    nic_files['nh'].update(shp_files['nh'])
    nic_files['sh'].update(shp_files['sh'])

    return nic_files


def pair_files(nic_ts, prd_ts):
    validation_pairs = OrderedDict()
    for hemis, tser in nic_ts.iteritems():

        validation_pairs[hemis] = []
        for timestamp, file in tser.iteritems():
            try:
                product_file = prd_ts[hemis][timestamp]
                validation_pairs[hemis].append((timestamp, file, product_file))
            except KeyError:
                # Do not consider pairs for which we do not have a product
                pass

    with open('/tmp/pairs.txt', 'w') as fp:
        json.dump(validation_pairs, fp)

    return validation_pairs


def year_of_interest(el):
    """
    Filter for years of interest filter function
    :param el:
        tuple of the form reference time, url string, url string
    :return:
    """
    return parser.parse(el[0]).year in cfg.YEARS_OF_INTEREST


def generate_time_series(description_str=''):

    # glob for all remote files
    prd_files = downloader.glob_file(cfg.METNO_THREDDS_DOWNL)
    # prd_files = downloader.glob_file(cfg.METNO_DOWNL)
    shp_files = downloader.glob_file(cfg.NIC_SHP_DOWNL)
    bin_files = downloader.glob_file(cfg.NIC_BIN_DOWNL)
    sig_files = downloader.glob_file(cfg.NIC_SIG_DOWNL)

    # generate time series
    prd_ts = generate_osi450_product_timeseries(prd_files)
    shp_ts = generate_nic_shp_timeseries(shp_files)
    bin_ts = generate_nic_bin_timeseries(bin_files)
    sig_ts = generate_nic_sig_timeseries(sig_files)
    nic_ts = generate_nic_timeseries(shp_ts, bin_ts, sig_ts)

    # generate time series mapping, i.e. tuples of ref_time, url_eval, url_data
    validation_pairs = pair_files(nic_ts, prd_ts)

    # filter file pairs so that only
    validation_pairs['nh'] = filter(year_of_interest, validation_pairs['nh'])
    validation_pairs['sh'] = filter(year_of_interest, validation_pairs['sh'])

    if '_NH_' in description_str:
        return validation_pairs['nh']
    elif '_SH_' in description_str:
        return validation_pairs['sh']

    return validation_pairs['nh'], validation_pairs['sh']
