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
      description        = (""),
      license            = 'GPL',
      long_description   = long_description,
      name               = 'pytracer', 
      test_suite         = 'nose.collector',
      version            = version,
      )
