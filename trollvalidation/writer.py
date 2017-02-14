from __future__ import division

import logging
import numpy as np
import numpy.ma as ma
import os
import json

from netCDF4 import Dataset

__authors__ = "John Lavelle, Luis Flores Vargas"
__organization__ = "Danish Meteorological Institute"
__email__ = "jol@dmi.dk"
__version__ = "0.1"

log = logging.getLogger(__name__)


class BUFR2NetCDFError(Exception):
    pass


class WriteNetCDF:
    
    FILL_VALUES = {
        'i4': -2147483648,
        'int': -2147483648,
        'uint64': 18446744073709551615,
        'uint32': 4294967295,
        'uint8': 255,
        'u1': 255,
        'long': 9223372036854775808,
        'int32': 2147483648,
        'f8': 1.70E+38,
        'float': -3.4028235e+38,
        'float64': -3.4028235e+38,
        'double': -3.4028235e+38,
        'f4': -3.4028235e+38,
        'i1': 2147483648,
        'str': 2147483648,
        'i2': -32767,
        'i4': -2147483648,
        'i8': -9223372036854775808
    }

    def __init__(self, path, replication=0):
        if os.path.isfile(path):
            self.root_grp = Dataset(path, 'r+', format='NETCDF4')
        else:
            self.root_grp = Dataset(path, 'w', format='NETCDF4')

        # Create basic dimensions in the NetCDF file
        # self.root_grp.createDimension('record', None)
        # self.root_grp.createDimension('scalar', 1)
        # self.root_grp.createDimension('record_repl_%d' % replication, None)

    def __enter__(self):
        return self

    @staticmethod
    def _nc_valid_var_type(var_type):
        return var_type in ['int', 'float', 'str', 'double', 'long']

    @staticmethod
    def netcdf_datatype(type_name):
        if 'float' in type_name:
            return 'f8'
        elif 'uint64' in type_name:
            return 'i8'
        elif 'int64' in type_name:
            return 'i8'
        elif 'uint32' in type_name:
            return 'i4'
        elif 'uint16' in type_name:
            return 'i4'
        elif 'uint8' in type_name:
            return 'u1'
        elif 'long' in type_name:
            return 'i4'
        elif 'string' in type_name:
            return 'i1'
        else:
            raise BUFR2NetCDFError("Cannot convert %s to NetCDF compatible type" % type_name)

    def create_global_attributes(self, title, institution, source, history, references,
                                 comments, conventions, contact=None):
        log.debug("Creating global attributes")

        self.root_grp.Conventions = conventions.encode('latin-1')
        self.root_grp.title = title.encode('latin-1')
        self.root_grp.institution = institution.encode('latin-1')
        self.root_grp.source = source.encode('latin-1')
        self.root_grp.history = history.encode('latin-1')
        self.root_grp.references = references.encode('latin-1')
        self.root_grp.comments = comments.encode('latin-1')
        if contact:
            self.root_grp.contact = contact.encode('latin-1')

    def create_variables(self, grp, dimension_option, name, var_type, unit, long_name, complevel=4,
                         least_significant_digit=6, calendar=None, fill_value='default'):
        # LOG.debug("Creating variable {}".format(name))

        ncvar_name = name

        # Guard ... dimension names cannot also be used as variable names
        # if ncvar_name in grp.dimensions:
        #     raise ValueError("Variable name %s also used as dimension name" % ncvar_name)

        # record_name = 'record'

        var_type = self.netcdf_datatype(var_type)

        fill_value = self.FILL_VALUES[var_type] if fill_value == 'default' else fill_value

        nc_var = grp.createVariable(
            ncvar_name,
            var_type,
            dimension_option,  # Pick 1: ('scalar',), (dimension_name, ), (record_name, ), (record_name, dimension_name)
            fill_value=fill_value,
            zlib=True,
            complevel=complevel,
            least_significant_digit=least_significant_digit,
            fletcher32=True)

        setattr(nc_var, 'units', unit)
        if long_name is not None:
            setattr(nc_var, 'long_name', long_name)
        if calendar:
            setattr(nc_var, 'calendar', calendar)

    def insert_record(self, grp, data, name, var_type, count=None):
        try:
            nc_var = grp.variables[name]
            var_type = var_type
            if not var_type in self.FILL_VALUES.keys():
                log.error("No valid type defined")
                return

            # Handle 32/64 numpy conversion
            # if 'int' in var_type:
            #     var_type = 'int32'
            # data = record.data
            # nc_var[count, :] = data.astype(var_type)

            nc_var[:] = data

        except ValueError, val_err:
            log.exception("Unable to insert records %s" % (val_err,))
            raise

    def df_to_nc(self, dataframe, dimension_name):

        if not (dimension_name in self.root_grp.dimensions):
            self.root_grp.createDimension(dimension_name, len(dataframe))

        for col in dataframe:
            if len(col) == 1:
                varname = col
                df = dataframe[varname]
                grp = self.root_grp
            elif len(col) == 2:
                if col[1] == '':
                    varname = col[0]
                    df = dataframe[varname]
                    grp = self.root_grp
                else:
                    grpname, varname = col
                    df = dataframe[grpname][varname]
                    grp = self.root_grp.createGroup(grpname)

            self.create_variables(grp, dimension_name, varname, 'float', '', '')
            self.insert_record(grp,  np.array(df), varname, 'float')

    def np_array_to_nc(self, data, variable_name, dimension_names, unit='', longname='',
                       dim_size=None, complevel=4, least_significant_digit=6, calendar=None,
                       fill_value='default'):
        for size, dimension_name in zip(*(data.shape, dimension_names)):
            if not (dimension_name in self.root_grp.dimensions):
                size = None if dim_size == 'unlimited' else size
                # log.debug('Creating dimension {0} for variable {1}'.format(dimension_name, variable_name))
                self.root_grp.createDimension(dimension_name, size)

        dtype = data.dtype.name
        self.create_variables(self.root_grp, dimension_names, variable_name, dtype, unit,
                              longname, complevel, least_significant_digit, calendar, fill_value)
        self.insert_record(self.root_grp, ma.masked_invalid(data), variable_name, dtype)

    def __exit__(self, exc_type, exc_value, traceback):
        self.root_grp.close()
