from setuptools import setup

version = '0.1.0'

import os
README = os.path.join(os.path.dirname(__file__), 'README.txt')
long_description = open(README).read() + '\n\n'

setup(
      author             = 'Rocky Bernstein',
      author_email       = 'rocky@gnu.org',
      classifiers        = [
              "Programming Language :: Python",
              ("Topic :: Software Development :: Libraries :: "
               "Python Modules"),
              ],
      description        = 'Centralized sys.settrace management',
      license            = 'GPL',
      long_description   = long_description,
      name               = 'pytracer', 
      py_modules         = ['tracer'],
      test_suite         = 'nose.collector',
      # url = 
      version            = version,
      )
