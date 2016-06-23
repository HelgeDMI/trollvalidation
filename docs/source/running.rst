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

  echo "from your_configuration import *" > ./validations/configuration.py



Finally, run the validation.

.. code-block:: bash

  python validations/your_validation.py


Running an example validation?
==============================


Currently, `trollvalidation` includes two validations that can be used for reference. They are both in the `validations` package. The first one `template_validation.py` is a simple validation, which generates an arbitrary timeseries (`generate_time_series()`) consisting entries for eight days and it compares the numpy array `np.array([1, 2, 3, 4])`, see `pre_func(ref_time, eval_file, orig_file)` with itself by computing the difference between the two. This validation can be used as a starting point when implementing other validations. You can run it as explained in the following:

Set the configuration to point to the template configuration...

.. code-block:: bash

  cd /path/to/trollvalidation/trollvalidation
  echo "from template_configuration import *" > ./validations/configuration.py


and run the validation.

.. code-block:: bash

  python ./validations/template_validation.py


On top of this example validation, there is a validation, which is used to validate two ice concentration products (OSI-401-b and OSI-409 products) in the OSI SAF project.


You can run the validation of ice concentration products as explained in the following:

Set the configuration to point to the ice concentration configuration...

.. code-block:: bash

  cd /path/to/trollvalidation/trollvalidation
  echo "from ice_conc_configuration import *" > ./validations/configuration.py


and run the validation.

.. code-block:: bash

  python ./validations/ice_conc_validation.py


Note, to run the validation you have to have `gdal-bin` installed with support for NetCDF files. If you are on a system, which uses `apt`for package management, then the configuration file should check that for you and should exit if you have not, see `ice_conc_configuration.py`. The ice concentration validation is a more complete example, which can be used for adaption when implementing your validation. A more detailed description of the ice concentration validation can be found [here]().
