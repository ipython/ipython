# -*- coding: utf-8 -*-
"""
======
Rmagic
======

Magic command interface for interactive work with R via rpy2

Usage
=====

``%R``

{R_DOC}

``%Rpush``

{RPUSH_DOC}

``%Rpull``

{RPULL_DOC}

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

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
from IPython.utils.py3compat import str_to_unicode, unicode_to_str

class RMagicError(ri.RRuntimeError):
    pass

@magics_class
class RMagics(Magics):
    """A set of magics useful for interactive work with R via rpy2.
    """

    def __init__(self, shell, Rconverter=np.asarray,
                 pyconverter=np.asarray,
                 cache_display_data=False):
        """
        Parameters
        ----------

        shell : IPython shell

        Rconverter : callable
            To be called on return values from R before returning 
            to ipython.

        pyconverter : callable
            To be called on values in ipython namespace before 
            assigning to variables in rpy2.

        cache_display_data : bool
            If True, the published results of the final call to R are 
            cached in the variable 'display_cache'.

        """
        super(RMagics, self).__init__(shell)
        self.cache_display_data = cache_display_data

        self.r = ro.R()
        self.Rstdout_cache = []
        self.Rconverter = Rconverter
        self.pyconverter = pyconverter

    def eval(self, line):
        '''
        Parse and evaluate a line with rpy2.
        Returns the output to R's stdout() connection
        and the value of eval(parse(line)).
        '''
        old_writeconsole = ri.get_writeconsole()
        ri.set_writeconsole(self.write_console)
        try:
            value = ri.baseenv['eval'](ri.parse(line))
        except (ri.RRuntimeError, ValueError) as exception:
            raise RMagicError(unicode_to_str('parsing and evaluating line "%s". R traceback: "%s"\n' %
                                             (line, str_to_unicode(exception.message, 'utf-8'))))
        text_output = self.flush()
        ri.set_writeconsole(old_writeconsole)
        return text_output, value

    def write_console(self, output):
        '''
        A hook to capture R's stdout in a cache.
        '''
        self.Rstdout_cache.append(output)

    def flush(self):
        '''
        Flush R's stdout cache to a string, returning the string.
        '''
        value = ''.join([str_to_unicode(s, 'utf-8') for s in self.Rstdout_cache])
        self.Rstdout_cache = []
        return value

    @skip_doctest
    @line_magic
    def Rpush(self, line):
        '''
        A line-level magic for R that pushes
        variables from python to rpy2. The line should be made up
        of whitespace separated variable names in the IPython
        namespace::

            In [7]: import numpy as np

            In [8]: X = np.array([4.5,6.3,7.9])

            In [9]: X.mean()
            Out[9]: 6.2333333333333343

            In [10]: %Rpush X

            In [11]: %R mean(X)
            Out[11]: array([ 6.23333333])

        '''

        inputs = line.split(' ')
        for input in inputs:
            self.r.assign(input, self.pyconverter(self.shell.user_ns[input]))

    @skip_doctest
    @line_magic
    def Rpull(self, line):
        '''
        A line-level magic for R that pulls
        variables from python to rpy2::

            In [18]: _ = %R x = c(3,4,6.7); y = c(4,6,7); z = c('a',3,4)

            In [19]: %Rpull x  y z

            In [20]: x
            Out[20]: array([ 3. ,  4. ,  6.7])

            In [21]: y
            Out[21]: array([ 4.,  6.,  7.])

            In [22]: z
            Out[22]:
            array(['a', '3', '4'],
                  dtype='|S1')


        Notes
        -----

        Beware that R names can have '.' so this is not fool proof.
        To avoid this, don't name your R objects with '.'s...

        '''
        outputs = line.split(' ')
        for output in outputs:
                self.shell.push({output:self.Rconverter(self.r(output))})


    @skip_doctest
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
        '-n', '--noreturn',
        help='Force the magic to not return anything.',
        action='store_true',
        default=False
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
        final line. Multiple R lines can be executed by joining them with semicolons::

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

        Objects can be passed back and forth between rpy2 and python via the -i -o flags in line::

            In [14]: Z = np.array([1,4,5,10])

            In [15]: %R -i Z mean(Z)
            Out[15]: array([ 5.])


            In [16]: %R -o W W=Z*mean(Z)
            Out[16]: array([  5.,  20.,  25.,  50.])

            In [17]: W
            Out[17]: array([  5.,  20.,  25.,  50.])

        The return value is determined by these rules:

        * If the cell is not None, the magic returns None.

        * If the cell evaluates as False, the resulting value is returned
        unless the final line prints something to the console, in
        which case None is returned.

        * If the final line results in a NULL value when evaluated
        by rpy2, then None is returned.


        '''

        args = parse_argstring(self.R, line)

        # arguments 'code' in line are prepended to
        # the cell lines
        if not cell:
            code = ''
            return_output = True
            line_mode = True
        else:
            code = cell
            return_output = False
            line_mode = False

        code = ' '.join(args.code) + code

        if args.input:
            for input in ','.join(args.input).split(','):
                self.r.assign(input, self.pyconverter(self.shell.user_ns[input]))

        png_argdict = dict([(n, getattr(args, n)) for n in ['units', 'height', 'width', 'bg', 'pointsize']])
        png_args = ','.join(['%s=%s' % (o,v) for o, v in png_argdict.items() if v is not None])
        # execute the R code in a temporary directory

        tmpd = tempfile.mkdtemp()
        self.r('png("%s/Rplots%%03d.png",%s)' % (tmpd, png_args))

        text_output = ''
        if line_mode:
            for line in code.split(';'):
                text_result, result = self.eval(line)
                text_output += text_result
            if text_result:
                # the last line printed something to the console so we won't return it
                return_output = False
        else:
            text_result, result = self.eval(code)
            text_output += text_result

        self.r('dev.off()')

        # read out all the saved .png files

        images = [open(imgfile, 'rb').read() for imgfile in glob("%s/Rplots*png" % tmpd)]

        # now publish the images
        # mimicking IPython/zmq/pylab/backend_inline.py
        fmt = 'png'
        mimetypes = { 'png' : 'image/png', 'svg' : 'image/svg+xml' }
        mime = mimetypes[fmt]

        # publish the printed R objects, if any

        display_data = []
        if text_output:
            display_data.append(('RMagic.R', {'text/plain':text_output}))

        # flush text streams before sending figures, helps a little with output
        for image in images:
            # synchronization in the console (though it's a bandaid, not a real sln)
            sys.stdout.flush(); sys.stderr.flush()
            display_data.append(('RMagic.R', {mime: image}))

        # kill the temporary directory
        rmtree(tmpd)

        # try to turn every output into a numpy array
        # this means that output are assumed to be castable
        # as numpy arrays

        if args.output:
            for output in ','.join(args.output).split(','):
                # with self.shell, we assign the values to variables in the shell
                self.shell.push({output:self.Rconverter(self.r(output))})

        for tag, disp_d in display_data:
            publish_display_data(tag, disp_d)

        # this will keep a reference to the display_data
        # which might be useful to other objects who happen to use
        # this method

        if self.cache_display_data:
            self.display_cache = display_data

        # if in line mode and return_output, return the result as an ndarray
        if return_output and not args.noreturn:
            if result != ri.NULL:
                return self.Rconverter(result)

__doc__ = __doc__.format(
                R_DOC = ' '*8 + RMagics.R.__doc__,
                RPUSH_DOC = ' '*8 + RMagics.Rpush.__doc__,
                RPULL_DOC = ' '*8 + RMagics.Rpull.__doc__
)


_loaded = False
def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(RMagics)
        _loaded = True
