#!/usr/bin/env python
"""
distutils setup (setup.py) for pytracer.

This gets a bit of package info from __pkginfo__.py file
"""
# Get the required package information 
from __pkginfo__ import author, author_email, classifiers, \
    license, modname, package_dir, \
    short_desc, version, web, zip_safe

from setuptools import setup

import os
top_dir = os.path.dirname(__file__)
README  = os.path.join(top_dir, 'README.txt')

# Description in package will come from the README file.
long_description = open(README).read() + '\n\n'

setup(
      author             = author,
      author_email       = author_email,
      classifiers        = classifiers,
      description        = short_desc,
      license            = license,
      long_description   = long_description,
      name               = modname,
      package_dir        = package_dir,
      py_modules         = ['tracer', 'tracefilter'],
      test_suite         = 'nose.collector',
      url                = web,
      version            = version,
      zip_safe           = zip_safe
      )
