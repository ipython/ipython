# -*- coding: utf-8 -*-
"""
R related magics.

Author:
* Jonathan Taylor

"""

import sys
import tempfile
from glob import glob
from shutil import rmtree
from getopt import getopt

# numpy and rpy2 imports

import numpy as np

import rpy2.rinterface as ri
import rpy2.robjects as ro
from rpy2.robjects.numpy2ri import numpy2ri
ro.conversion.py2ri = numpy2ri

# IPython imports

from IPython.core.displaypub import publish_display_data
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic,
                                line_cell_magic)
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)

@magics_class
class RMagics(Magics):

    def __init__(self, shell, Rconverter=np.asarray,
                 pyconverter=np.asarray):
        super(RMagics, self).__init__(shell)
        ri.set_writeconsole(self.write_console)

        # the embedded R process from rpy2
        self.r = ro.R()
        self.output = []
        self.Rconverter = Rconverter
        self.pyconverter = pyconverter

    def eval(self, line):
        try:
            return ri.baseenv['eval'](ri.parse(line))
        except (ri.RRuntimeError, ValueError) as msg:
            self.output.append('ERROR parsing "%s": %s\n' % (line, msg))
            pass

    def write_console(self, output):
        '''
        A hook to capture R's stdout.
        '''
        self.output.append(output)

    def flush(self):
        value = ''.join([s.decode('utf-8') for s in self.output])
        self.output = []
        return value

    @line_magic
    def Rpush(self, line):
        '''
        A line-level magic for R that pushes
        variables from python to rpy2.

        Parameters
        ----------

        line: input

              A white space separated string of
              names of objects in the python name space to be
              assigned to objects of the same name in the
              R name space.

        '''

        inputs = line.split(' ')
        for input in inputs:
            self.r.assign(input, self.pyconverter(self.shell.user_ns[input]))

    @line_magic
    def Rpull(self, line):
        '''
        A line-level magic for R that pulls
        variables from python to rpy2.

        Parameters
        ----------

        line: output

              A white space separated string of
              names of objects in the R name space to be
              assigned to objects of the same name in the
              python name space.

        Notes
        -----

        Beware that R names can have '.' so this is not fool proof.
        To avoid this, don't name your R objects with '.'s...

        '''
        outputs = line.split(' ')
        for output in outputs:
                self.shell.push({output:self.Rconverter(self.r(output))})


    @magic_arguments()
    @argument(
        '-i', '--input', action='append',
        help='Names of input variable from shell.user_ns to be assigned to R variables of the same names after calling self.pyconverter. Multiple names can be passed separated only by commas with no whitespace.'
        )
    @argument(
        '-o', '--output', action='append',
        help='Names of variables to be pushed from rpy2 to shell.user_ns after executing cell body and applying self.Rconverter. Multiple names can be passed separated only by commas with no whitespace.'
        )
    @argument(
        '-w', '--width', type=int,
        help='Width of png plotting device sent as an argument to *png* in R.'
        )
    @argument(
        '-h', '--height', type=int,
        help='Height of png plotting device sent as an argument to *png* in R.'
        )

    @argument(
        '-u', '--units', type=int,
        help='Units of png plotting device sent as an argument to *png* in R. One of ["px", "in", "cm", "mm"].'
        )
    @argument(
        '-p', '--pointsize', type=int,
        help='Pointsize of png plotting device sent as an argument to *png* in R.'
        )
    @argument(
        '-b', '--bg',
        help='Background of png plotting device sent as an argument to *png* in R.'
        )
    @argument(
        'code',
        nargs='*',
        )
    @line_cell_magic
    def R(self, line, cell=None):
        '''
        Execute code in R, and pull some of the results back into the Python namespace.

        In line mode, this will evaluate an expression and convert the returned value to a Python object.
        The return value is determined by rpy2's behaviour of returning the result of evaluating the
        final line. Multiple R lines can be executed by joining them with semicolons.

        In [9]: %R X=c(1,4,5,7); sd(X); mean(X)
        Out[9]: array([ 4.25])

        As a cell, this will run a block of R code, without bringing anything back by default::

        In [10]: %%R
           ....: Y = c(2,4,3,9)
           ....: print(summary(lm(Y~X)))
           ....:

        Call:
        lm(formula = Y ~ X)

        Residuals:
            1     2     3     4
         0.88 -0.24 -2.28  1.64

        Coefficients:
                    Estimate Std. Error t value Pr(>|t|)
        (Intercept)   0.0800     2.3000   0.035    0.975
        X             1.0400     0.4822   2.157    0.164

        Residual standard error: 2.088 on 2 degrees of freedom
        Multiple R-squared: 0.6993,Adjusted R-squared: 0.549
        F-statistic: 4.651 on 1 and 2 DF,  p-value: 0.1638

        In the notebook, plots are published as the output of the cell.

        %R plot(X, Y)

        will create a scatter plot of X bs Y.

        If cell is not None and line has some R code, it is prepended to
        the R code in cell.

        Objects can be passed back and forth between rpy2 and python via the -i -o flags in line


        In [14]: Z = np.array([1,4,5,10])

        In [15]: %R -i Z mean(Z)
        Out[15]: array([ 5.])


        In [16]: %R -o W W=Z*mean(Z)
        Out[16]: array([  5.,  20.,  25.,  50.])

        In [17]: W
        Out[17]: array([  5.,  20.,  25.,  50.])

        If the cell is None, the resulting value is returned,
        after conversion with self.Rconverter
        unless the line has contents that are published to the ipython
        notebook (i.e. plots are create or something is printed to
        R's stdout() connection).

        If the cell is not None, the magic returns None.

        '''

        args = parse_argstring(self.R, line)

        # arguments 'code' in line are prepended to
        # the cell lines
        if not cell:
            code = ''
            return_output = True
        else:
            code = cell
            return_output = False

        code = ' '.join(args.code) + code

        if args.input:
            for input in ','.join(args.input).split(','):
                self.r.assign(input, self.pyconverter(self.shell.user_ns[input]))

        png_argdict = dict([(n, getattr(args, n)) for n in ['units', 'height', 'width', 'bg', 'pointsize']])
        png_args = ','.join(['%s=%s' % (o,v) for o, v in png_argdict.items() if v is not None])
        # execute the R code in a temporary directory

        tmpd = tempfile.mkdtemp()
        self.r('png("%s/Rplots%%03d.png",%s)' % (tmpd, png_args))
        result = self.eval(code)
        self.r('dev.off()')

        # read out all the saved .png files

        images = [open(imgfile, 'rb').read() for imgfile in glob("%s/Rplots*png" % tmpd)]

        # now publish the images
        # mimicking IPython/zmq/pylab/backend_inline.py
        fmt = 'png'
        mimetypes = { 'png' : 'image/png', 'svg' : 'image/svg+xml' }
        mime = mimetypes[fmt]

        published = False
        # publish the printed R objects, if any
        flush = self.flush()
        if flush:
            published = True
            publish_display_data('RMagic.R', {'text/plain':flush})

        # flush text streams before sending figures, helps a little with output
        for image in images:
            published = True
            # synchronization in the console (though it's a bandaid, not a real sln)
            sys.stdout.flush(); sys.stderr.flush()
            publish_display_data(
                'RMagic.R',
                {mime : image}
            )
        value = {}

        # try to turn every output into a numpy array
        # this means that output are assumed to be castable
        # as numpy arrays

        if args.output:
            for output in ','.join(args.output).split(','):
                # with self.shell, we assign the values to variables in the shell
                self.shell.push({output:self.Rconverter(self.r(output))})

        # kill the temporary directory
        rmtree(tmpd)

        # if there was a single line, return its value
        # converted to a python object

        if return_output and not published:
            return self.Rconverter(result)

_loaded = False
def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(RMagics)
        _loaded = True
