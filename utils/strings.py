 """String utilities.

Contains a collection of usefull string manipulations functions.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Our own imports
import textwrap #TODO

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def wrap(text, width=100):
    """ Try to detect and wrap paragraph"""

    splitt = text.split('\n')
    wrp = map(lambda x:textwrap.wrap(x,width),splitt)
    wrpd = map('\n'.join, wrp)
    return '\n'.join(wrpd)