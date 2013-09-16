# -*- coding: utf-8 -*-
"""
======
Rmagic
======

Magic command interface for interactive work with R via rpy2

.. note::

  The ``rpy2`` package needs to be installed separately. It
  can be obtained using ``easy_install`` or ``pip``.

  You will also need a working copy of R.

Usage
=====

To enable the magics below, execute ``%load_ext rmagic``.

``%R``

{R_DOC}

``%Rpush``

{RPUSH_DOC}

``%Rpull``

{RPULL_DOC}

``%Rget``

{RGET_DOC}

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

# numpy and rpy2 imports

import numpy as np

import rpy2.rinterface as ri
import rpy2.robjects as ro
try:
    from rpy2.robjects import pandas2ri
    pandas2ri.activate()
except ImportError:
    pandas2ri = None
    from rpy2.robjects import numpy2ri
    numpy2ri.activate()

# IPython imports

from IPython.core.displaypub import publish_display_data
from IPython.core.magic import (Magics, magics_class, line_magic,
                                line_cell_magic, needs_local_scope)
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)
from IPython.external.simplegeneric import generic
from IPython.utils.py3compat import str_to_unicode, unicode_to_str, PY3

class RInterpreterError(ri.RRuntimeError):
    """An error when running R code in a %%R magic cell."""
    def __init__(self, line, err, stdout):
        self.line = line
        self.err = err.rstrip()
        self.stdout = stdout.rstrip()
    
    def __unicode__(self):
        s = 'Failed to parse and evaluate line %r.\nR error message: %r' % \
                (self.line, self.err)
        if self.stdout and (self.stdout != self.err):
            s += '\nR stdout:\n' + self.stdout
        return s
    
    if PY3:
        __str__ = __unicode__
    else:
        def __str__(self):
            return unicode_to_str(unicode(self), 'utf-8')

def Rconverter(Robj, dataframe=False):
    """
    Convert an object in R's namespace to one suitable
    for ipython's namespace.

    For a data.frame, it tries to return a structured array.
    It first checks for colnames, then names.
    If all are NULL, it returns np.asarray(Robj), else
    it tries to construct a recarray

    Parameters
    ----------

    Robj: an R object returned from rpy2
    """
    is_data_frame = ro.r('is.data.frame')
    colnames = ro.r('colnames')
    rownames = ro.r('rownames') # with pandas, these could be used for the index
    names = ro.r('names')

    if dataframe:
        as_data_frame = ro.r('as.data.frame')
        cols = colnames(Robj)
        _names = names(Robj)
        if cols != ri.NULL:
            Robj = as_data_frame(Robj)
            names = tuple(np.array(cols))
        elif _names != ri.NULL:
            names = tuple(np.array(_names))
        else: # failed to find names
            return np.asarray(Robj)
        Robj = np.rec.fromarrays(Robj, names = names)
    return np.asarray(Robj)

@generic
def pyconverter(pyobj):
    """Convert Python objects to R objects. Add types using the decorator:
    
    @pyconverter.when_type
    """
    return pyobj

# The default conversion for lists seems to make them a nested list. That has
# some advantages, but is rarely convenient, so for interactive use, we convert
# lists to a numpy array, which becomes an R vector.
@pyconverter.when_type(list)
def pyconverter_list(pyobj):
    return np.asarray(pyobj)

if pandas2ri is None:
    # pandas2ri was new in rpy2 2.3.3, so for now we'll fallback to pandas'
    # conversion function.
    try:
        from pandas import DataFrame
        from pandas.rpy.common import convert_to_r_dataframe
        @pyconverter.when_type(DataFrame)
        def pyconverter_dataframe(pyobj):
            return convert_to_r_dataframe(pyobj, strings_as_factors=True)
    except ImportError:
        pass

@magics_class
class RMagics(Magics):
    """A set of magics useful for interactive work with R via rpy2.
    """

    def __init__(self, shell, Rconverter=Rconverter,
                 pyconverter=pyconverter,
                 cache_display_data=False):
        """
        Parameters
        ----------

        shell : IPython shell
        
        Rconverter : callable
            To be called on values taken from R before putting them in the
            IPython namespace.

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
        self.pyconverter = pyconverter
        self.Rconverter = Rconverter

    def eval(self, line):
        '''
        Parse and evaluate a line of R code with rpy2.
        Returns the output to R's stdout() connection, 
        the value generated by evaluating the code, and a
        boolean indicating whether the return value would be
        visible if the line of code were evaluated in an R REPL.
        
        R Code evaluation and visibility determination are
        done via an R call of the form withVisible({<code>})
        
        '''
        old_writeconsole = ri.get_writeconsole()
        ri.set_writeconsole(self.write_console)
        try:
            res = ro.r("withVisible({%s})" % line)
            value = res[0] #value (R object)
            visible = ro.conversion.ri2py(res[1])[0] #visible (boolean)
        except (ri.RRuntimeError, ValueError) as exception:
            warning_or_other_msg = self.flush() # otherwise next return seems to have copy of error
            raise RInterpreterError(line, str_to_unicode(str(exception)), warning_or_other_msg)
        text_output = self.flush()
        ri.set_writeconsole(old_writeconsole)
        return text_output, value, visible

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
    @needs_local_scope
    @line_magic
    def Rpush(self, line, local_ns=None):
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
        if local_ns is None:
            local_ns = {}

        inputs = line.split(' ')
        for input in inputs:
            try:
                val = local_ns[input]
            except KeyError:
                try:
                    val = self.shell.user_ns[input]
                except KeyError:
                    # reraise the KeyError as a NameError so that it looks like
                    # the standard python behavior when you use an unnamed
                    # variable
                    raise NameError("name '%s' is not defined" % input)

            self.r.assign(input, self.pyconverter(val))

    @skip_doctest
    @magic_arguments()
    @argument(
        '-d', '--as_dataframe', action='store_true',
        default=False,
        help='Convert objects to data.frames before returning to ipython.'
        )
    @argument(
        'outputs',
        nargs='*',
        )
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


        If --as_dataframe, then each object is returned as a structured array
        after first passed through "as.data.frame" in R before
        being calling self.Rconverter. 
        This is useful when a structured array is desired as output, or
        when the object in R has mixed data types. 
        See the %%R docstring for more examples.

        Notes
        -----

        Beware that R names can have '.' so this is not fool proof.
        To avoid this, don't name your R objects with '.'s...

        '''
        args = parse_argstring(self.Rpull, line)
        outputs = args.outputs
        for output in outputs:
            self.shell.push({output:self.Rconverter(self.r(output),dataframe=args.as_dataframe)})

    @skip_doctest
    @magic_arguments()
    @argument(
        '-d', '--as_dataframe', action='store_true',
        default=False,
        help='Convert objects to data.frames before returning to ipython.'
        )
    @argument(
        'output',
        nargs=1,
        type=str,
        )
    @line_magic
    def Rget(self, line):
        '''
        Return an object from rpy2, possibly as a structured array (if possible).
        Similar to Rpull except only one argument is accepted and the value is 
        returned rather than pushed to self.shell.user_ns::

            In [3]: dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')]

            In [4]: datapy = np.array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c'), (4, 5, 'e')], dtype=dtype)

            In [5]: %R -i datapy

            In [6]: %Rget datapy
            Out[6]: 
            array([['1', '2', '3', '4'],
                   ['2', '3', '2', '5'],
                   ['a', 'b', 'c', 'e']], 
                  dtype='|S1')

            In [7]: %Rget -d datapy
            Out[7]: 
            array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c'), (4, 5.0, 'e')], 
                  dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')])

        '''
        args = parse_argstring(self.Rget, line)
        output = args.output
        return self.Rconverter(self.r(output[0]),dataframe=args.as_dataframe)


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
        '-d', '--dataframe', action='append',
        help='Convert these objects to data.frames and return as structured arrays.'
        )
    @argument(
        '-u', '--units', type=unicode, choices=["px", "in", "cm", "mm"],
        help='Units of png plotting device sent as an argument to *png* in R. One of ["px", "in", "cm", "mm"].'
        )
    @argument(
        '-r', '--res', type=int,
        help='Resolution of png plotting device sent as an argument to *png* in R. Defaults to 72 if *units* is one of ["in", "cm", "mm"].'
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
    @needs_local_scope
    @line_cell_magic
    def R(self, line, cell=None, local_ns=None):
        '''
        Execute code in R, and pull some of the results back into the Python namespace.

        In line mode, this will evaluate an expression and convert the returned value to a Python object.
        The return value is determined by rpy2's behaviour of returning the result of evaluating the
        final line. 

        Multiple R lines can be executed by joining them with semicolons::

            In [9]: %R X=c(1,4,5,7); sd(X); mean(X)
            Out[9]: array([ 4.25])

        In cell mode, this will run a block of R code. The resulting value
        is printed if it would printed be when evaluating the same code 
        within a standard R REPL.
        
        Nothing is returned to python by default in cell mode::

            In [10]: %%R
               ....: Y = c(2,4,3,9)
               ....: summary(lm(Y~X))

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

        In the notebook, plots are published as the output of the cell::

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

        * No attempt is made to convert the final value to a structured array.
          Use the --dataframe flag or %Rget to push / return a structured array.

        * If the -n flag is present, there is no return value.

        * A trailing ';' will also result in no return value as the last
          value in the line is an empty string.

        The --dataframe argument will attempt to return structured arrays. 
        This is useful for dataframes with
        mixed data types. Note also that for a data.frame, 
        if it is returned as an ndarray, it is transposed::

            In [18]: dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')]

            In [19]: datapy = np.array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c'), (4, 5, 'e')], dtype=dtype)

            In [20]: %%R -o datar
            datar = datapy
               ....: 

            In [21]: datar
            Out[21]: 
            array([['1', '2', '3', '4'],
                   ['2', '3', '2', '5'],
                   ['a', 'b', 'c', 'e']], 
                  dtype='|S1')

            In [22]: %%R -d datar
            datar = datapy
               ....: 

            In [23]: datar
            Out[23]: 
            array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c'), (4, 5.0, 'e')], 
                  dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')])

        The --dataframe argument first tries colnames, then names.
        If both are NULL, it returns an ndarray (i.e. unstructured)::

            In [1]: %R mydata=c(4,6,8.3); NULL

            In [2]: %R -d mydata

            In [3]: mydata
            Out[3]: array([ 4. ,  6. ,  8.3])

            In [4]: %R names(mydata) = c('a','b','c'); NULL

            In [5]: %R -d mydata

            In [6]: mydata
            Out[6]: 
            array((4.0, 6.0, 8.3), 
                  dtype=[('a', '<f8'), ('b', '<f8'), ('c', '<f8')])

            In [7]: %R -o mydata

            In [8]: mydata
            Out[8]: array([ 4. ,  6. ,  8.3])

        '''

        args = parse_argstring(self.R, line)

        # arguments 'code' in line are prepended to
        # the cell lines

        if cell is None:
            code = ''
            return_output = True
            line_mode = True
        else:
            code = cell
            return_output = False
            line_mode = False

        code = ' '.join(args.code) + code

        # if there is no local namespace then default to an empty dict
        if local_ns is None:
            local_ns = {}

        if args.input:
            for input in ','.join(args.input).split(','):
                try:
                    val = local_ns[input]
                except KeyError:
                    try:
                        val = self.shell.user_ns[input]
                    except KeyError:
                        raise NameError("name '%s' is not defined" % input)
                self.r.assign(input, self.pyconverter(val))

        if getattr(args, 'units') is not None:
            if args.units != "px" and getattr(args, 'res') is None:
                args.res = 72
            args.units = '"%s"' % args.units

        png_argdict = dict([(n, getattr(args, n)) for n in ['units', 'res', 'height', 'width', 'bg', 'pointsize']])
        png_args = ','.join(['%s=%s' % (o,v) for o, v in png_argdict.items() if v is not None])
        # execute the R code in a temporary directory

        tmpd = tempfile.mkdtemp()
        self.r('png("%s/Rplots%%03d.png",%s)' % (tmpd.replace('\\', '/'), png_args))

        text_output = ''
        try:
            if line_mode:
                for line in code.split(';'):
                    text_result, result, visible = self.eval(line)
                    text_output += text_result
                if text_result:
                    # the last line printed something to the console so we won't return it
                    return_output = False
            else:
                text_result, result, visible = self.eval(code)
                text_output += text_result
                if visible:
                    old_writeconsole = ri.get_writeconsole()
                    ri.set_writeconsole(self.write_console) 
                    ro.r.show(result)
                    text_output += self.flush()
                    ri.set_writeconsole(old_writeconsole)
        
        except RInterpreterError as e:
            print(e.stdout)
            if not e.stdout.endswith(e.err):
                print(e.err)
            rmtree(tmpd)
            return

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
                self.shell.push({output:self.Rconverter(self.r(output), dataframe=False)})

        if args.dataframe:
            for output in ','.join(args.dataframe).split(','):
                self.shell.push({output:self.Rconverter(self.r(output), dataframe=True)})

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
                return self.Rconverter(result, dataframe=False)

__doc__ = __doc__.format(
                R_DOC = ' '*8 + RMagics.R.__doc__,
                RPUSH_DOC = ' '*8 + RMagics.Rpush.__doc__,
                RPULL_DOC = ' '*8 + RMagics.Rpull.__doc__,
                RGET_DOC = ' '*8 + RMagics.Rget.__doc__
)


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(RMagics)
    # Initialising rpy2 interferes with readline. Since, at this point, we've
    # probably just loaded rpy2, we reset the delimiters. See issue gh-2759.
    if ip.has_readline:
        ip.readline.set_completer_delims(ip.readline_delims)
