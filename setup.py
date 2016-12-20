from setuptools import setup, find_packages
import sys

requirements = ['pyresample', 'numpy', 'funcsigs', 'pandas']

setup(name='trollvalidation',
      version=1.0,
      description='A system for validation of meteorological satellite products.',
      author='Helge Pfeiffer',
      author_email='rhp@dmi.dk',
      packages=find_packages(exclude=['docs']),
      install_requires=requirements,
      package_data={
        '': [
            'etc/areas.cfg',]
      },
      zip_safe=False,
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: Apache 2.0',
          'Programming Language :: Python',
          'Operating System :: OS Independent',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering'
      ]
)
