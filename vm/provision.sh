#!/bin/bash

sudo locale-gen UTF-8
sudo apt-get -y install python-pip git
sudo apt-get -y install python-dev libnetcdf-dev libhdf5-dev
sudo apt-get -y install gdal-bin lftp
sudo apt-get -y install python-distutils-extra

sudo pip install suplemon

echo "Creating directories for validation data..."
mkdir -p validation/data/input/tmp
mkdir -p validation/data/output

curl -sL https://raw.githubusercontent.com/brainsik/virtualenv-burrito/master/virtualenv-burrito.sh | $SHELL
source /home/vagrant/.venvburrito/startup.sh

mkvirtualenv validation

echo "Setting up Python environment..."
pip install pyresample
pip install pykdtree
pip install funcsigs
pip install numpy
pip install pandas
pip install netCDF4
pip install ipython[notebook]
toggleglobalsitepackages
pip install python-apt

echo "Cloning from Github..."
cd validation
git clone https://github.com/HelgeDMI/trollvalidation.git

# workon validation
# add2virtualenv ./trollvalidation/trollvalidation/
# add2virtualenv does not seem to work...
sed -i '/^import sys; sys.__plen = len(sys.path)/a\/home/vagrant/validation/trollvalidation/trollvalidation' ~/.virtualenvs/validation/lib/python2.7/site-packages/_virtualenv_path_extensions.pth

echo "Now do:"
echo "add2virtualenv ~/validation/trollvalidation/trollvalidation"
echo "cd validation/trollvalidation/trollvalidation"
echo "workon validation"
echo "python validations/ice_conc_validation.py"
