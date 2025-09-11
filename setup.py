#!/usr/bin/env python
"""
distutils setup (setup.py) for pytracer.

This gets a bit of package info from __pkginfo__.py file
# Get the required package information
"""
from __pkginfo__ import \
    author,           author_email,       classifiers,                    \
    license,          long_description,   modname,                        \
    short_desc,       version,            web,              zip_safe

from setuptools import find_packages, setup

import os

top_dir = os.path.dirname(__file__)
README  = os.path.join(top_dir, "README.rst")

# Description in package will come from the README file.
long_description = open(README).read() + "\n\n"

__import__("pkg_resources")

packages = find_packages()

setup(
      author             = author,
      author_email       = author_email,
      classifiers        = classifiers,
      description        = short_desc,
      license            = license,
      long_description   = long_description,
      name               = modname,
      packages=packages,
      py_modules         = ["tracer", "tracer.tracefilter", "tracer"],
      test_suite         = 'nose.collector',
      url                = web,
      version            = version,
      zip_safe           = zip_safe
      )
