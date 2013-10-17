"""Utilities to manipulate Javascript files.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING.txt, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import glob
import os

from IPython.display import display, Javascript

#-----------------------------------------------------------------------------
# Methods
#-----------------------------------------------------------------------------

def display_all_js(directory):
    
    # Display each javascript file in the directory.
    for filename in glob.glob(os.path.join(directory, '*.js')):
        with open(filename, 'r') as f:
            display(Javascript(data=f.read()))
