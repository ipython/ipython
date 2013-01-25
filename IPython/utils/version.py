# encoding: utf-8
"""
Utilities for version comparison

It is a bit ridiculous that we need these.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from distutils.version import LooseVersion

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

class NumericalVersion(LooseVersion):
    """A version of LooseVersion that is *always* comparable
    
    String elements (of any kind!) are interpreted as infinite.
    Since these are generally only on development branches,
    that is fairly safe, even though technically 1.0a1 should be less than 1.0.
    """
    def parse (self, vstring):
        # I've given up on thinking I can reconstruct the version string
        # from the parsed tuple -- so I just store the string here for
        # use by __str__
        self.vstring = vstring
        components = filter(lambda x: x and x != '.',
                            self.component_re.split(vstring))
        for i in range(len(components)):
            try:
                components[i] = int(components[i])
            except ValueError:
                # this is the only change
                components[i] = float('inf')

        self.version = components

def version_tuple(vs):
    """Return a tuple of numbers from a version string.
    
    'dev' 'a', 'etc' are transformed to float('inf'),
    so they will always compare positively to any
    regular integer element.
    """
    return tuple(NumericalVersion(vs).version)
    