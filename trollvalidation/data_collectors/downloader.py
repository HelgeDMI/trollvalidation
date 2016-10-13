import datetime
import json
import logging
import os
import re
import shlex
import sys
import urllib2
from subprocess import Popen, PIPE
from urllib2 import urlopen

from trollvalidation.validations import configuration as cfg

LOG = logging.getLogger('nic_downloader')


def get(remote_file, local_path=cfg.INPUT_DIR, report_hook=None):
    fname = os.path.basename(remote_file)
    target = os.path.join(local_path, fname)

    if not os.path.isfile(target):
        LOG.info('Download {0} to {1}'.format(remote_file, target))
        try:
            # Replaced urlretrieve as it did not close connections properly,
            # so there remained to many open preventing the rest of the
            # validation step to pass
            # urllib.urlretrieve(remote_file, filename=target,
            #                    reporthook=report_hook)

            remote_file_content = urllib2.urlopen(remote_file)
            with open(target, 'wb') as output:
                output.write(remote_file_content.read())
        except IOError, e:
            LOG.exception(e)
            LOG.error('Could not download file {0}'.format(remote_file))

    return target


def reporthook(a, b, c):
    # from: http://stackoverflow.com/a/2003565
    sys.stdout.write("\r% 3.1f%% of %d bytes" % (min(100, float(a * b) / c *
                                                     100), c))
    sys.stdout.flush()


def get_html_page(host, path):
    # Construct url and read content
    url = 'http://{0}/{1}'.format(host, path)
    html_content = urlopen(url).read()
    return html_content


def find_links(in_text, with_pattern):
    return re.findall(with_pattern, in_text)


def extract_timestamp(from_string, with_r_pattern, with_date_pattern):
    time_str = re.search(with_r_pattern, from_string).group()
    timestamp = datetime.datetime.strptime(time_str, with_date_pattern)
    return timestamp


def scrape_all(http_cfg):
    glob = []
    for hemis, path in http_cfg['remote_html_path'].iteritems():
        # open remote html file
        html_contents = get_html_page(http_cfg['host'], http_cfg[
            'remote_html_path'][hemis])
        # get all the links out of this
        links = find_links(html_contents, http_cfg['remote_link_pattern'][
            hemis])

        regexp_date = http_cfg['remote_date_pattern'][0]
        date_pattern = http_cfg['remote_date_pattern'][1]
        time_series = \
            [extract_timestamp(l, regexp_date, date_pattern) for l in links]

        dates = filter(lambda d: (d.year in cfg.YEARS_OF_INTEREST), time_series)

        # finally, construct remote file links
        # creates a list of years and of time strings in the given format
        year_strs = map(lambda d: datetime.datetime.strftime(d, '%Y'),
                        dates)
        time_strs = map(lambda d: datetime.datetime.strftime(d, '%y%m%d'),
                        dates)
        # generate a list of complete links
        remote_files = map(lambda year, time: http_cfg['remote_file_pattern'][
            hemis].format(year, time), year_strs, time_strs)

        glob += remote_files

    return glob


def glob_all(host, remote_dir, user=None, pwd=None, port=None,
             protocol='ftp://'):
    if protocol == 'sftp://':
        cmd = 'lftp -e "glob -f echo {0}; bye" -p {1} -u {2},{3} {4}{5}'
        cmd = cmd.format(remote_dir, port, user, pwd, host)
    elif protocol == 'ftp://' or protocol == 'http://':
        cmd = 'lftp -e "glob -f echo {0}; bye" {1}{2}'
        cmd = cmd.format(remote_dir, protocol, host)
    process = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    out_d, err_d = process.communicate()

    remote_file_list = []
    if out_d:
        remote_file_list = out_d.split()

    return remote_file_list

def generate_all(protocol, host, remote_dir_f_pattern, date_range):

    remote_file_list = [os.path.join(protocol, host, remote_dir_f_pattern.format(d.year, d.month, h, datetime.strftime(d, '%Y%m%d'))) for d in date_range for h in ['n', 's']]

    return remote_file_list



def glob_file(cfg):
    if 'scrape' not in cfg.keys():
        cfg['scrape'] = False
    if 'generate' not in cfg.keys():
        cfg['generate'] = False
    if 'user' not in cfg.keys():
        cfg['user'] = None
    if 'pwd' not in cfg.keys():
        cfg['pwd'] = None
    if 'port' not in cfg.keys():
        cfg['port'] = None

    if not os.path.isfile(cfg['glob_file']):
        if not cfg['scrape']:
            if not 'generate' in cfg.keys():
                LOG.info('Globbing remote files from HTTP/FTP')
                remote_files = glob_all(cfg['host'],
                                        cfg['remote_dir_f_pattern'],
                                        cfg['user'], cfg['pwd'], cfg['port'],
                                        cfg['protocol'])
            else:
                remote_files = generate_all(cfg['protocol'], cfg['host'],
                                            cfg['remote_dir_f_pattern'],
                                            cfg['generate'])
        elif cfg['scrape']:
            remote_files = scrape_all(cfg)


        # attach protocol and host
        remote_files = ['{0}{1}/{2}'.format(cfg['protocol'], cfg[
            'host'], f) for f in remote_files]

        with open(cfg['glob_file'], 'w') as fp:
            json.dump(remote_files, fp)
    else:
        LOG.info('Globbing remote files from file')
        with open(cfg['glob_file']) as fp:
            remote_files = json.load(fp)

    return remote_files
