`trollvalidation` is a Python package for implementing validations particularly of products derived meteorological satellite data.

`trollvalidation` does not provide a strict framework for implementing validations. Instead, it is more a collection of helper functions and -together with this documentation- provides a collection of best practices.



Install
=======

Currently, the project is not on PyPi. So either install it manually by 


```bash
pip install trollplot --no-index --find-links file:///path/to/trollvalidation/dist/trollvalidation-1.0.tar.gz
```
or 
```bash
cd /path/to/trollvalidation/dist/trollvalidation-1.0.tar.gz
python setup.py install
```


Alternatively, you can clone the repository:


```bash
git clone https://github.com/HelgeDMI/trollvalidation.git

```

Subsequently, add `trollvalidation` to your Python path. In case you are using `virtualenv-wrapper`:

```bash
add2virtualenv /path/to/trollvalidation
```


Requirements
============

  * Tested with Python 2.7.11
  * Numpy (`pip install numpy`)
  * Pandas (`pip install pandas`)
  * Pyresample (`pip install pyresample`)
  * funcsigs (`pip install funcsigs`)
  * LFTP on your `PATH` (`apt-get install lftp`)
  * (for `ice_conc_validation.py` you will need `gdal-bin` installed.
  Especially, you will need `gdal_rasterize` with NetCDF support.)



Usage
=====

```bash
cd /path/to/trollvalidation/trollvalidation/
python ./valdations/your_validation.py
```


How do I implement my own validations?
======================================

Read more about implementing your own validations and the systems architecture in the `docs` folder. As soon as the documentation is finalized, it will be moved to readthedocs.