Design Goals of `trollvalidation`
=================================

With `trollvalidation` we aim to address and implement the following goals:

  * **Simplicity**,  a validation needs to be simple enough so that each stakeholder, scientist and software engineers are able to grasp the function and the purpose of those parts of the validation system that are most important to them.
  * **Traceability**, a validation system should automatise all steps from data retrieval over data conversion to computation of validation results, so that validations can be reproduced on various computers by various stake.


What is a validation?
=====================

The purpose of this section is to define the terms and concepts which are important for the `trollvalidation` system. Furthermore, we detail what we consider a validation and what the `trollvalidation` system currently implements.

In all generality, we consider a *validation* to be an operation which computes a set of metrics on a set of files and a set of corresponding reference files. Consequently, the task of a *validation system* is to




Original Data
-------------

Original data is the dataset -usually in the realm of meteorological satellite products a set of files-, which is produced by your meteorological satellite data processing system. For example, in the OSI SAF project the various sea ice concentration, sea ice type, etc. products are original data respectively or in the NWC SAF the cloud mask, cloud type, etc. products are original data.


Evaluation Data
---------------

Evaluation data is the dataset -again usually a set of files-, which is used as reference, i.e., to which teh original data is compared to.


Timeseries
----------

A time series interrelates a evaluation and original data with respect to a reference time.

For example, in the OSI SAF project sea ice concentration products are compared to NIC ice charts. Currently, an ice concentration validation compares the NIC ice chart for a given day with the corresponding ice concentration product. Similarly, in the NWC SAF project a cloud mask over a three minute Metop AVHRR segment might be compared to a corresponding
CALIPSO meassurement.

Technically, a timeseries is a list of tuples containing a reference time, a URL to evaluation data, and a URL to the original data. For example, the following code snippet contains the first three entries for the timeseries interelating NIC ice charts and reprocessed OSI SAF ice concentration products corresponding to the northern hemisphere and the year 2014.


.. code-block:: python

[('2014-01-07',
  'http://www.natice.noaa.gov/pub/weekly/arctic/2014/shapefiles/hemispheric/arctic140107.zip',
  'ftp://osisaf.met.no/reprocessed/ice/conc/v1p2/2014/01/ice_conc_nh_ease-125_reproc_201401071200.nc.gz'),
 ('2014-01-09',
  'http://www.natice.noaa.gov/pub/weekly/arctic/2014/shapefiles/hemispheric/arctic140109.zip',
  'ftp://osisaf.met.no/reprocessed/ice/conc/v1p2/2014/01/ice_conc_nh_ease-125_reproc_201401091200.nc.gz'),
 ('2014-01-14', u'http://www.natice.noaa.gov/pub/weekly/arctic/2014/shapefiles/hemispheric/arctic140114.zip',
  'ftp://osisaf.met.no/reprocessed/ice/conc/v1p2/2014/01/ice_conc_nh_ease-125_reproc_201401141200.nc.gz'),
  ...
]




There a re three concepts, which are important for `trollvalidation`. These are a *Validation Task*, a *Validation Step*, and a *Validation Function*. Additionally,

The three concepts are detailed in the following.




Validation Task
---------------

A validation task is the task of comparing a set of satellite products with a reference dataset.

For example, imagine a colleague saying: "We have to compute biases and standard deviations for the OSI SAF ice concentration products compared to NIC ice charts for the year 2015 and for both, the northern and the southern hemisphere." That is a validation task. More precisely in our understanding it is two validation tasks. One for the northern and one for the southern
hemisphere. But that is a question of interpretation and can be implemented differently.

The validation task contains many validation steps.

It is a collection of validation steps for an evaluation dataset and an original dataset.


Validation Step
---------------




Validation Function
-------------------

A validation function is a function, which computes a metric incorporating both the evaluation and the original data. For example, the OIOIOI





Timeseries can relate many-to-many evaluation and original datasets.
