# Copyright (C) 2008, 2009, 2010 Rocky Bernstein <rocky@gnu.org>
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

copyright   = '''Copyright (C) 2008, 2009, 2010 Rocky Bernstein <rocky@gnu.org>.'''
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
import os.path
# VERSION.py sets variable VERSION.
execfile(os.path.join(os.path.dirname(__file__), 'VERSION.py'))

version      = VERSION
web          = 'http://code.google.com/p/pytracer'

package_dir  = {'': 'tracer'}

zip_safe     = False # tracebacks in zip files are funky and not debuggable

import os
def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()
long_description   = ( read("README.txt") + '\n\n' +  read("NEWS") )
