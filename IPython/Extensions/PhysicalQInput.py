# -*- coding: utf-8 -*-
"""Modified input prompt for entering quantities with units.

Modify the behavior of the interactive interpreter to allow direct input of
quantities with units without having to make a function call.

Now the following forms are accepted:

x = 4 m
y = -.45e3 m/s
g = 9.8 m/s**2
a = 2.3 m/s^2   # ^ -> ** automatically

All other input is processed normally.
"""
#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

# This file is an example of how to modify IPython's line-processing behavior
# without touching the internal code. We'll define an alternate pre-processing
# stage which allows a special form of input (which is invalid Python syntax)
# for certain quantities, rewrites a line of proper Python in those cases, and
# then passes it off to IPython's normal processor for further work.

# With this kind of customization, IPython can be adapted for many
# special-purpose scenarios providing alternate input syntaxes.

# This file can be imported like a regular module.

# IPython has a prefilter() function that analyzes each input line. We redefine
# it here to first pre-process certain forms of input

# The prototype of any alternate prefilter must be like this one (the name
# doesn't matter):
# - line is a string containing the user input line.
# - continuation is a parameter which tells us if we are processing a first line of
#   user input or the second or higher of a multi-line statement.

def prefilter_PQ(self,line,continuation):
    """Alternate prefilter for input of PhysicalQuantityInteractive objects.

    This assumes that the function PhysicalQuantityInteractive() has been
    imported."""

    from re import match
    from IPython.iplib import InteractiveShell

    # This regexp is what does the real work
    unit_split = match(r'\s*(\w+)\s*=\s*(-?\d*\.?\d*[eE]?-?\d*)\s+([a-zA-Z].*)',
                       line)

    # If special input was ecnountered, process it:
    if unit_split:
        var,val,units = unit_split.groups()
        if var and val and units:
            units = units.replace('^','**')
            # Now a valid line needs to be constructed for IPython to process:
            line = var +" = PhysicalQuantityInteractive(" + val + ", '" + \
                   units + "')"
            #print 'New line:',line   # dbg
            
    # In the end, always call the default IPython _prefilter() function.  Note
    # that self must be passed explicitly, b/c we're calling the unbound class
    # method (since this method will overwrite the instance prefilter())
    return InteractiveShell._prefilter(self,line,continuation)

# Rebind this to be the new IPython prefilter:
from IPython.iplib import InteractiveShell
InteractiveShell.prefilter = prefilter_PQ

# Clean up the namespace.
del InteractiveShell,prefilter_PQ

# Just a heads up at the console
print '*** Simplified input for physical quantities enabled.'
