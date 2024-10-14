|CircleCI| |Pypi Installs| |Latest Version| |Supported Python Versions|

|packagestatus|

Centralized Trace management using ``sys.settrace``.

We allow several trace hooks to get registered and unregistered and
allow tracing to be turned on and off temporarily without losing the
trace hooks. You can also indicate filters on events for which trace
hooks should fire and mark methods that should automatically be
ignored.

Installation
------------

This package is available from PyPI::

    $ pip install tracer

However if you want to install from the github source::

    $ pip install       # creates wheel and install

To run from the source tree::

    $ pip install -e .  # set up to run from source tree


Support of older versions of Python
-----------------------------------

We support running this from older versions of Python in various git branches:

* ``python-2.4-to-2.7`` has code for Python 2.4 to 2.7
* ``python-3.0-to-3.2`` has code for Python 3.0 to 3.2
* ``python-3.3-to-3.5`` has code for Python 3.3 to 3.5
* ``python-3.6-to-3.10`` has code for Python 3.6 to 3.10
* ``master`` has code for Python 3.11 to the current version of Python


.. |CircleCI| image:: https://circleci.com/gh/rocky/pytracer.svg?style=svg
.. _features: https://github.com/rocky/pytracer/blob/master/NEW-FEATURES.rst
.. _directory: https://github.com/rocky/pytracer/tree/master/example
.. _uncompyle6: https://pypi.python.org/pypi/uncompyle6/
.. |downloads| image:: https://img.shields.io/pypi/dd/spark.svg
.. |buildstatus| image:: https://travis-ci.org/rocky/pytracer.svg :target: https://travis-ci.org/rocky/pytracer
.. |Supported Python Versions| image:: https://img.shields.io/pypi/pyversions/spark_parser.svg
.. |Latest Version| image:: https://badge.fury.io/py/tracer.svg :target: https://badge.fury.io/py/pytracer
.. |Pypi Installs| image:: https://pepy.tech/badge/pytracer/month
.. |packagestatus| image:: https://repology.org/badge/vertical-allrepos/python:spark.svg :target: https://repology.org/project/python:tracer/versions
