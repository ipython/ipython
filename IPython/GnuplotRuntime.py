# -*- coding: utf-8 -*-
"""Basic Gnuplot functionality for inclusion in other code.

This module creates a running Gnuplot instance called 'gp' and builds other
convenient globals for quick use in running scripts. It is intended to allow
you to script plotting tasks in Python with a minimum of effort. A typical
usage would be:

import IPython.GnuplotRuntime as GP  # or some other short name
GP.gp.plot(GP.File('your_data.dat'))


This module exposes the following objects:

- gp: a running Gnuplot instance. You can access its methods as
gp.<method>. gp(`a string`) will execute the given string as if it had been
typed in an interactive gnuplot window.

- gp_new: a function which returns a new Gnuplot instance. This can be used to
have multiple Gnuplot instances running in your session to compare different
plots.

- Gnuplot: alias to the Gnuplot2 module, an improved drop-in replacement for
the original Gnuplot.py. Gnuplot2 needs Gnuplot but redefines several of its
functions with improved versions (Gnuplot2 comes with IPython).

- Data: alias to Gnuplot.Data, makes a PlotItem from array data.

- File: alias to Gnuplot.File, makes a PlotItem from a file.

- String: alias to Gnuplot.String, makes a PlotItem from a string formatted
exactly like a file for Gnuplot.File would be.

- Func: alias to Gnuplot.Func, makes a PlotItem from a function string.

- GridData: alias to Gnuplot.GridData, makes a PlotItem from grid data.

- pm3d_config: a string with Gnuplot commands to set up the pm3d mode for
surface plotting. You can activate it simply by calling gp(pm3d_config).

- eps_fix_bbox: A Unix-only function to fix eps files with bad bounding boxes
(which Gnuplot generates when the plot size is set to square).

This requires the Gnuplot.py module for interfacing Python with Gnuplot, which
can be downloaded from:

http://gnuplot-py.sourceforge.net/

Inspired by a suggestion/request from Arnd Baecker.

$Id: GnuplotRuntime.py 389 2004-10-09 07:59:30Z fperez $"""

__all__ = ['Gnuplot','gp','gp_new','Data','File','Func','GridData',
           'pm3d_config','eps_fix_bbox']

import os,tempfile,sys
from IPython.genutils import getoutput

#---------------------------------------------------------------------------
# Notes on mouse support for Gnuplot.py

# If you do not have a mouse-enabled gnuplot, set gnuplot_mouse to 0. If you
# use gnuplot, you should really grab a recent, mouse enabled copy. It is an
# extremely useful feature.  Mouse support is official as of gnuplot 4.0,
# released in April 2004.

# For the mouse features to work correctly, you MUST set your Gnuplot.py
# module to use temporary files instead of 'inline data' for data
# communication. Note that this is the default, so unless you've manually
# fiddled with it you should be ok. If you need to make changes, in the
# Gnuplot module directory, loook for the gp_unix.py file and make sure the
# prefer_inline_data variable is set to 0. If you set it to 1 Gnuplot.py will
# try to pass the data to gnuplot via standard input, which completely
# confuses the mouse control system (even though it may be a bit faster than
# using temp files).

# As of Gnuplot.py v1.7, a new option was added to use FIFOs (pipes).  This
# mechanism, while fast, also breaks the mouse system.  You must therefore set
# the variable prefer_fifo_data to 0 in gp_unix.py.

tmpname = tempfile.mktemp()
open(tmpname,'w').write('set mouse')
gnu_out = getoutput('gnuplot '+ tmpname)
os.unlink(tmpname)
if gnu_out:  # Gnuplot won't print anything if it has mouse support
    print "*** Your version of Gnuplot appears not to have mouse support."
    gnuplot_mouse = 0
else:
    gnuplot_mouse = 1
del tmpname,gnu_out

# Default state for persistence of new gnuplot instances
if os.name in ['nt','dos'] or sys.platform == 'cygwin':
    gnuplot_persist = 0
else:
    gnuplot_persist = 1

import IPython.Gnuplot2 as Gnuplot

class NotGiven: pass

def gp_new(mouse=NotGiven,persist=NotGiven):
    """Return a new Gnuplot instance.

    The instance returned uses the improved methods defined in Gnuplot2.

    Options (boolean):

    - mouse: if unspecified, the module global gnuplot_mouse is used.

    - persist: if unspecified, the module global gnuplot_persist is used."""
    
    if mouse is NotGiven:
        mouse = gnuplot_mouse
    if persist is NotGiven:
        persist = gnuplot_persist
    g = Gnuplot.Gnuplot(persist=persist)
    if mouse:
        g('set mouse')
    return g

# Global-level names.

# A global Gnuplot instance for interactive use:
gp = gp_new()

# Accessors for the main plot object constructors:
Data = Gnuplot.Data
File = Gnuplot.File
Func = Gnuplot.Func
String = Gnuplot.String
GridData = Gnuplot.GridData

# A Unix-only function to fix eps files with bad bounding boxes (which Gnuplot
# generates when the plot size is set to square):
eps_fix_bbox = Gnuplot.eps_fix_bbox

# String for configuring pm3d. Simply call g(pm3d_config) to execute it.  pm3d
# is a very nice mode for plotting colormaps on surfaces. Modify the defaults
# below to suit your taste.
pm3d_config = """
set pm3d solid
set hidden3d
unset surface
set isosamples 50
"""
#******************** End of file <GnuplotRuntime.py> ******************
