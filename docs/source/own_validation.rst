How do I write my own validation?
=================================

  * Start from an existing validation and adapt it to your needs.
  * Create a `your_validation_configuration.py` file, which points to the various data sources, and local paths.
  * Make the global configuration file `configuration.py` point to your configuration file. (echo "from your_configuration import *" > ./validations/configuration.py)
  * Implement your own validation in `your_validation.py`.
    
    * Start by implementing a *pre-validation task*, e.g., a time series generator. The current time series generator `data_collectors/tseries_generator.py` allows for globbing from FTP servers and globbing via scraping from HTTP pages. It expects that the evaluation and original data contains some form of a timestamp in the filename.
    * The time series generator has to return a a list of tuples of the form `[(timestamp_str, eval_data_url, orig_data_url), ...]`
    * Implement a *pre-validation step*, i.e., a subprogram, which prepares the evaluation and the original data for validation. That is, implement a program, which downloads each file type, uncompresses them if necessary, and reads the data out of the files.
    * Implement your validation functions and place them in `your_val_step(ref_time, data_eval, data_orig)` in `your_validation.py`.


That should be it for validation of file-based products. The following sections detail how to customize the system for slightly different use cases.


My data is on a non-public FTP server
-------------------------------------

The current validation system allows for downloading files from FTP servers for which you have to provide credentials. A configuration for the `downloader` may contain three additional optional fields `port`, `user`, `pwd`. A corresponding configuration may look as in the following:


.. code-block:: python

	NIC_BIN_DOWNL = {
	    'protocol': 'ftp://',
	    'host': 'your.fileserver.org',
	    'remote_dir_f_pattern': 'pub/datasets/file_*_.bin',
	    'remote_date_pattern': (r'\d{4}_\d{2}_\d{2}', '%Y_%m_%d'),
	    'glob_file': os.path.join(TMP_DIR, 'your_files.json'),
	    'port': 2051,
	    'user': 'your_user_name',
	    'pwd': 'your_password'
	}




I have a database and no files containing my validation data
------------------------------------------------------------


I have a set of validation files, which I want to compare against a single original file
----------------------------------------------------------------------------------------

