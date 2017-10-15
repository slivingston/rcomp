#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup


# Version
# N.B., this is versioned separately from rcompserv
MAJOR = 0
MINOR = 1
MICRO = 0

rcomp_version = '{major}.{minor}.{micro}'.format(major=MAJOR, minor=MINOR, micro=MICRO)

with open('rcomp/_version.py', 'w') as f:
    f.write("""# Automatically generated by setup.py of rcomp. Do not edit.
version = '{version}'""".format(version=rcomp_version))


setup(name='rcomp',
      version=rcomp_version,
      author='Scott C. Livingston',
      author_email='slivingston@cds.caltech.edu',
      url='https://github.com/slivingston/rcomp',
      license='BSD',
      description='',
      packages=['rcomp'],
      install_requires=['requests'],
      entry_points={'console_scripts': ['rcomp = rcomp.cli:main']},
      classifiers=['Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5']
      )