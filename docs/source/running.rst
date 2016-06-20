Requirements
============

  * Tested with Python 2.7.11
  * Numpy (`pip install numpy`)
  * Pandas (`pip install pandas`)
  * Pyresample (`pip install pyresample`)
  * LFTP on your `PATH` (`apt-get install lftp`)
  * (for `ice_conc_validation.py` you will need `gdal-bin` installed.
  Especially, you will need `gdal_rasterize` with NetCDF support.)


How do I run a validation?
==========================

First, clone the project.

.. code-block:: bash

  git clone https://github.com/HelgeDMI/trollvalidation.git
  cd trollvalidation
  add2virtualenv ./trollvalidation



Subsequently,  configure the configuration file for you validation.

.. code-block:: bash

  echo "from your_validation import *" > ./validations/configuration.py



Finally, run the validation.

.. code-block:: bash

  python validations/your_validation.py
