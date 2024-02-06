# Copyright (C) 2008-2010, 2015, 2024
# Rocky Bernstein <rocky@gnu.org>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""pytracer packaging information"""

import os.path as osp

copyright   = '''Copyright (C) 2008-2010, 2015 Rocky Bernstein <rocky@gnu.org>.'''
classifiers =  ['Development Status :: 4 - Beta',
                'Environment :: Console',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Topic :: Software Development :: Debuggers',
                'Topic :: Software Development :: Libraries :: Python Modules',
                ]

# The rest in alphabetic order
author       = "Rocky Bernstein"
author_email = "rocky@gnu.org"

ftp_url      = None
license      = 'GPL'
modname      = 'tracer'

short_desc   = 'Centralized sys.settrace management'
# __version__.py sets variable __version__.

def get_srcdir():
    filename = osp.normcase(osp.dirname(osp.abspath(__file__)))
    return osp.realpath(filename)


def read(*rnames):
    return open(osp.join(get_srcdir(), *rnames)).read()


exec(read("tracer", "version.py"))

version      = __version__
web          = 'http://github.com/rocky/pytracer'

package_dir  = {'': 'tracer'}

# tracebacks in zip files are funky and not debuggable
zip_safe     = False

def read(*rnames):
    return open(osp.join(osp.dirname(__file__), *rnames)).read()

long_description   = ( read("README.rst") + '\n' )
