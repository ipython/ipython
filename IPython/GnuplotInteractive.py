# -*- coding: utf-8 -*-
"""Interactive functions and magic functions for Gnuplot usage.

This requires the Gnuplot.py module for interfacing python with Gnuplot, which
can be downloaded from:

http://gnuplot-py.sourceforge.net/

See gphelp() below for details on the services offered by this module.

Inspired by a suggestion/request from Arnd Baecker.

$Id: GnuplotInteractive.py 389 2004-10-09 07:59:30Z fperez $"""

__all__ = ['Gnuplot','gp','gp_new','plot','plot2','splot','replot',
           'hardcopy','gpdata','gpfile','gpstring','gpfunc','gpgrid',
           'gphelp']

import IPython.GnuplotRuntime as GRun
from IPython.genutils import page,warn

# Set global names for interactive use
Gnuplot  = GRun.Gnuplot
gp_new   = GRun.gp_new
gp       = GRun.gp
plot     = gp.plot
plot2    = gp.plot2
splot    = gp.splot
replot   = gp.replot
hardcopy = gp.hardcopy

# Accessors for the main plot object constructors:
gpdata   = Gnuplot.Data
gpfile   = Gnuplot.File
gpstring = Gnuplot.String
gpfunc   = Gnuplot.Func
gpgrid   = Gnuplot.GridData

def gphelp():
    """Print information about the Gnuplot facilities in IPython."""

    page("""
IPython provides an interface to access the Gnuplot scientific plotting
system, in an environment similar to that of Mathematica or Matlab.

New top-level global objects
----------------------------

Please see their respective docstrings for further details.

- gp: a running Gnuplot instance. You can access its methods as
gp.<method>. gp(`a string`) will execute the given string as if it had been
typed in an interactive gnuplot window.

- plot, splot, replot and hardcopy: aliases to the methods of the same name in
the global running Gnuplot instance gp. These allow you to simply type:

In [1]: plot(x,sin(x),title='Sin(x)')  # assuming x is a Numeric array

and obtain a plot of sin(x) vs x with the title 'Sin(x)'.

- gp_new: a function which returns a new Gnuplot instance. This can be used to
have multiple Gnuplot instances running in your session to compare different
plots, each in a separate window.

- Gnuplot: alias to the Gnuplot2 module, an improved drop-in replacement for
the original Gnuplot.py. Gnuplot2 needs Gnuplot but redefines several of its
functions with improved versions (Gnuplot2 comes with IPython).

- gpdata, gpfile, gpstring, gpfunc, gpgrid: aliases to Gnuplot.Data,
Gnuplot.File, Gnuplot.String, Gnuplot.Func and Gnuplot.GridData
respectively. These functions create objects which can then be passed to the
plotting commands. See the Gnuplot.py documentation for details.

Keep in mind that all commands passed to a Gnuplot instance are executed in
the Gnuplot namespace, where no Python variables exist. For example, for
plotting sin(x) vs x as above, typing

In [2]: gp('plot x,sin(x)')

would not work. Instead, you would get the plot of BOTH the functions 'x' and
'sin(x)', since Gnuplot doesn't know about the 'x' Python array. The plot()
method lives in python and does know about these variables.


New magic functions
-------------------

%gpc: pass one command to Gnuplot and execute it or open a Gnuplot shell where
each line of input is executed.

%gp_set_default: reset the value of IPython's global Gnuplot instance.""")
    
# Code below is all for IPython use
# Define the magic functions for communicating with the above gnuplot instance.
def magic_gpc(self,parameter_s=''):
    """Execute a gnuplot command or open a gnuplot shell.

    Usage (omit the % if automagic is on). There are two ways to use it:

      1) %gpc 'command' -> passes 'command' directly to the gnuplot instance.

      2) %gpc -> will open up a prompt (gnuplot>>>) which takes input like the
      standard gnuplot interactive prompt. If you need to type a multi-line
      command, use \\ at the end of each intermediate line.

      Upon exiting of the gnuplot sub-shell, you return to your IPython
      session (the gnuplot sub-shell can be invoked as many times as needed).
      """

    if parameter_s.strip():
        self.shell.gnuplot(parameter_s)
    else:
        self.shell.gnuplot.interact()

def magic_gp_set_default(self,parameter_s=''):
    """Set the default gnuplot instance accessed by the %gp magic function.

    %gp_set_default name

    Call with the name of the new instance at the command line. If you want to
    set this instance in your own code (using an embedded IPython, for
    example), simply set the variable __IPYTHON__.gnuplot to your own gnuplot
    instance object."""

    gname = parameter_s.strip()
    G = eval(gname,self.shell.user_ns)
    self.shell.gnuplot = G
    self.shell.user_ns.update({'plot':G.plot,'splot':G.splot,'plot2':G.plot2,
                               'replot':G.replot,'hardcopy':G.hardcopy})

try:
    __IPYTHON__
except NameError:
    pass
else:
    # make the global Gnuplot instance known to IPython
    __IPYTHON__.gnuplot = GRun.gp
    __IPYTHON__.gnuplot.shell_first_time = 1

    print """*** Type `gphelp` for help on the Gnuplot integration features."""

    # Add the new magic functions to the class dict
    from IPython.iplib import InteractiveShell
    InteractiveShell.magic_gpc = magic_gpc
    InteractiveShell.magic_gp_set_default = magic_gp_set_default

#********************** End of file <GnuplotInteractive.py> *******************
