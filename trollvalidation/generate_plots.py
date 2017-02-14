# This script will be removed soon and integrated more generically into
# validation_utils.py


import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import glob
import os
import logging
import configuration as cfg

LOG = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG,
#                     format='[%(levelname)s: %(asctime)s: %(name)s] %(message)s',
#                     datefmt='%Y-%m-%d %H:%M:%S')

image_format = 'png'


def line_plot(dates, values, styles, title, ylabel, legend, ylim, format, path):
    """Returns matplotlib line plot as StringIO object.

    Arguments:
    dates  -- List of dates
    values -- List of datasets. Each dataset is a list
    styles -- List of style codes. One element for each dataset
    title  -- Plot title
    ylabel -- Plot y-axis label
    legend -- List of plot legend. One element for each dataset
    ylim   -- Y-axis limits as typle: (y_min, y_max)
    format -- Image format
    """
    dates_mpl = matplotlib.dates.date2num(dates)

    plots = []
    i = 0
    for item in values:
        plots.append(plt.plot(dates_mpl, item, styles[i]))
        i += 1

    _set_line_plot(dates)

    return _get_plot(plots, dates, title, ylabel, legend, ylim, format, path)


def bar_side_plot(dates, values, colors, title, ylabel, legend, width, format,
                  path):
    """Returns matplotlib bar side plot as StringIO object.

    Arguments:
    dates  -- List of dates
    values -- List of datasets. Each dataset is a list
    colors -- List of color codes. One element for each dataset
    title  -- Plot title
    ylabel -- Plot y-axis label
    legend -- List of plot legend. One element for each dataset
    width  -- Width of bars in number of days
    format -- Image format
    """

    dates_mpl = matplotlib.dates.date2num(dates)

    plots = []
    i = 0
    for item in values:
        plots.append(plt.bar(dates_mpl + i*width, item, width,
                             color=colors[i], edgecolor=colors[i]))
        i += 1

    _set_bar_plot(dates, width)
    return _get_plot(plots, dates, title, ylabel, legend, (0, 200), format,
                     path)


def get_reduced_dates(dates, max_count=30):
    """If number of dates is greater than 'max_count' a reduced dataset is
    returned with 'max_count' number of dates evenly spaced

    Arguments:
    dates -- A list of datetimes
    max_count -- Threshold for reducing

    Returns: mpl_dates_reduced,display_dates
    mpl_dates_reduced -- Reduced dataset as mpl dates
    display_dates     -- String representation of dates as '%Y-%m-%d'
    """

    dates_mpl = matplotlib.dates.date2num(dates)
    disp_dates = []

    if len(dates) > max_count:
        dt = float(dates_mpl[-1] - dates_mpl[0])/(max_count - 1)
        dates_mpl_reduced = [dates_mpl[0] + dt*i for i in range(max_count)]
    else:
        dates_mpl_reduced = dates_mpl

    for num_date in dates_mpl_reduced:
        date = matplotlib.dates.num2date(num_date)
        disp_dates.append(date.strftime('%Y-%m-%d'))

    return np.array(dates_mpl_reduced), disp_dates


def _set_line_plot(dates):
    # Set line plot specific properties

    # Reduce number of dates if needed and get display dates
    dates_mpl, disp_dates = get_reduced_dates(dates)

    plt.xticks(dates_mpl, disp_dates, rotation=45, fontsize=8)
    plt.xlim((dates_mpl[0], dates_mpl[-1]))
    plt.gca().yaxis.grid(True)


def _set_bar_plot(dates, width):
    # Set bar plot specific properties

    # Reduce number of dates if needed and get display dates
    dates_mpl, disp_dates = get_reduced_dates(dates)

    plt.yticks(np.arange(0, 101, 10))
    plt.xticks(dates_mpl + width/2.0, disp_dates, rotation=45, fontsize=8)
    plt.xlim(dates_mpl[0] - width, dates_mpl[-1] + 2*width)


def _get_plot(plots, dates, title, ylabel, legend, ylim, format, path):
    # Set general plot properties
    plt.ylim(ylim)
    plt.ylabel(ylabel)

    plt.title(title)

    plot_list = []
    for item in plots:
        plot_list.append(item[0])

    prop = matplotlib.font_manager.FontProperties(size=8)
    plt.legend(plot_list, legend, prop=prop)
    plt.savefig(path, format=format)
    plt.clf()
    return plt


def generate_plot_names(reportname, plot_suffix):
    filename = os.path.basename(reportname)
    path = os.path.dirname(reportname)
    new_filename = "%s_%s.%s" % (filename.split('.')[0], plot_suffix,
                                 image_format)
    new_filename = os.path.join(path, new_filename)
    return new_filename


def generate_plots(directory):
    reports = glob.glob(os.path.join(directory, "*.csv"))
    print("Found {0}".format(reports))
    for report in reports:
        # if os.path.basename(report).startswith('OSI401_'):
        print('Generating... {0}'.format(report))
        try:
            generate_plots_per_report(report)
        except Exception, e:
            LOG.exception(e)


def generate_plots_per_report(report):
    # read CSV file
    data = np.genfromtxt(report, delimiter=',', dtype="U75", skip_header=1)

    fmt = '%Y-%m-%d'
    # to_float = lambda s: float(s or np.nan)
    # to_date = lambda s: datetime.strptime(s, fmt)
    # converters = {
    #     0: to_date, 1: to_date, 2: to_date,
    #     3: to_float, 4: to_float, 5: to_float, 6: to_float, 7: to_float,
    #     8: to_float, 9: to_float, 10: to_float
    # }
    # data = np.genfromtxt(report, delimiter=',', dtype="U75", skip_header=1,
    #           missing_values='--', converters=converters)
    #
    #
    # data = np.genfromtxt(report, delimiter=',', dtype=None,
    #                      skip_header=1, missing_values='--',
    #                      filling_values=-999.0, converters=converters)
    # data

    # data = data[data.argsort()]  # Sort by the 1st column

    # df = pd.read_csv(report, index_col=0, parse_dates=True, na_values='--')

    # Sort the validation results after reference time, just to be sure in
    # case the CSV file is unsorted

    data = data[data[:, 0].argsort()]  # Sort by the 1st column

    # header from CSV file
    # 'reference_time', 'run_time', 'total_bias', 'ice_bias', 'water_bias',
    # 'total_stddev', 'ice_stddev', 'water_stddev', 'within_10pct',
    # 'within_20pct'
    dates = [datetime.strptime(d, fmt) for d in data[:, 1]]

    total_bias = [-999 if v == '--' else float(v) for v in data[:, -8]]
    ice_bias = [-999 if v == '--' else float(v) for v in data[:, -7]]
    water_bias = [-999 if v == '--' else float(v) for v in data[:, -6]]

    total_stddev = [-999 if v == '--' else float(v) for v in data[:, -5]]
    ice_stddev = [-999 if v == '--' else float(v) for v in data[:, -4]]
    water_stddev = [-999 if v == '--' else float(v) for v in data[:, -3]]

    witin_10pct = [-999 if v == '--' else float(v) for v in data[:, -2]]
    witin_20pct = [-999 if v == '--' else float(v) for v in data[:, -1]]

    plot_name = generate_plot_names(report, 'match')
    bar_side_plot(dates, [witin_20pct, witin_10pct], ['0.1', '0.7'],
                  'Sea Ice Concentration', 'Fraction of grid points (%)',
                  ['Match +/-20%', 'Match +/-10%'], 1, image_format, plot_name)

    plot_name = generate_plot_names(report, 'bias')
    line_plot(dates, [water_bias, ice_bias, total_bias],
              ['bo-', 'rs--', 'k^:'], 'Bias of sea ice concentration',
              '% concentration', ['Water', 'Ice', 'Total'], (-20, 15),
              image_format, plot_name)
    plot_name = generate_plot_names(report, 'stddev')
    line_plot(dates, [water_stddev, ice_stddev, total_stddev],
              ['bo-', 'rs--', 'k^:'],
              'Standard deviation of sea ice concentration',
              'Std. dev (% concentration)', ['Water', 'Ice', 'Total'], (0, 30),
              image_format, plot_name)

if __name__ == '__main__':
    generate_plots(cfg.OUTPUT_DIR)
