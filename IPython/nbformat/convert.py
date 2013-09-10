"""API for converting notebooks between versions.

Authors:

* Jonathan Frederic
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import re

import IPython.nbformat as nbformat

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# Get the convert modules for each major revision.
VERSION_REGEX = re.compile("v[0-9]+")
version_modules = {}
for module in dir(nbformat):
    if VERSION_REGEX.match(module):
        version_modules[int(module[1:])] = eval('nbformat.' + module + '.convert')

# Get the number of minor versions in each major version and create an ordered
# list.
versions = []
for major in version_modules.keys().sort():
    current_minor = 0
    if hasattr(version_modules[major], 'nbformat_minor'):
        current_minor = version_modules[major].nbformat_minor

    for minor in range(0, current_minor + 1):
        versions.append((major, minor))

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def convert(nb, to_major, to_minor=0):
    """Convert a notebook node object to a specific version"""

    # Get input notebook version.
    major = nb.get('nbformat', 1)
    minor = nb.get('nbformat_minor', 0) # v3+

    # Check if destination is current version, if so return contents
    if to_major == major and to_minor == minor:
        return nb
    elif (to_major, to_minor) in versions:
        index = versions.indexof((major, minor))

        if to_major > major or (to_major == major and to_minor > minor):
            to_index = index + 1
        else:
            to_index = index - 1

    else:
        raise Exception("Cannot convert notebook to v%d.%d because that version doesn't exist" % (to_major, to_minor))