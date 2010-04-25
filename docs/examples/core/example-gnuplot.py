#!/usr/bin/env python
"""
Example code showing how to use Gnuplot and an embedded IPython shell.
"""

from Numeric import *
from IPython.numutils import *
from IPython.Shell import IPShellEmbed

# Arguments to start IPython shell with. Load numeric profile.
ipargs = ['-profile','numeric']
ipshell = IPShellEmbed(ipargs)

# Compute sin(x) over the 0..2pi range at 200 points
x = frange(0,2*pi,npts=200)
y = sin(x)

# In the 'numeric' profile, IPython has an internal gnuplot instance:
g = ipshell.IP.gnuplot

# Change some defaults
g('set style data lines')

# Or also call a multi-line set of gnuplot commands on it:
g("""
set xrange [0:pi]     # Set the visible range to half the data only
set title 'Half sine' # Global gnuplot labels
set xlabel 'theta'
set ylabel 'sin(theta)'
""")

# Now start an embedded ipython.
ipshell('Starting the embedded IPython.\n'
        'Try calling plot(x,y), or @gpc for direct access to Gnuplot"\n')

#********************** End of file <example-gnuplot.py> *********************
