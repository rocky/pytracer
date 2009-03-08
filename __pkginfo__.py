# Copyright (C) 2008 Rocky Bernstein <rocky@gnu.org>
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

modname = 'tracer'

numversion = (0, 2, 2)
version = '.'.join([str(num) for num in numversion])

license = 'GPL'
copyright = '''Copyright (C) 2008, 2009 Rocky Bernstein <rocky@gnu.org>.'''

short_desc = 'Centralized sys.settrace management'

author = "Rocky Bernstein"
author_email = "rocky@gnu.org"

web = 'http://code.google.com/p/pytracer'

classifiers =  ['Development Status :: 4 - Beta',
                'Environment :: Console',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Operating System :: OS Independent',
                'Programming Language :: Python',
                'Topic :: Software Development :: Debuggers',
                'Topic :: Software Development :: Libraries :: Python Modules',
                ]

package_dir = {'': 'tracer'}

zip_safe = False # tracebacks in zip files are funky and not debuggable
