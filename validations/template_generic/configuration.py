import os

CSV_HEADER = ['reference_time', 'run_time', 'my_val']
BASE_PATH = '/tmp'
INPUT_DIR = os.path.join(BASE_PATH, 'ice_chart_data')
TMP_DIR = os.path.join(BASE_PATH, 'ice_chart_data', 'tmp')
OUTPUT_DIR = os.path.join(BASE_PATH, 'ice_chart_output')
