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

``%Rget``

{RGET_DOC}

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import sys, json, os
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

from IPython.core.page import page
from IPython.core.displaypub import publish_display_data
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic,
                                line_cell_magic, needs_local_scope)
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)
from IPython.utils.py3compat import str_to_unicode, unicode_to_str, PY3
from IPython.utils.io import capture_output

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

@magics_class
class RMagics(Magics):
    """A set of magics useful for interactive work with R via rpy2.
    """

    def __init__(self, shell, Rconverter=Rconverter,
                 pyconverter=np.asarray,
                 cache_display_data=False):
        """
        Parameters
        ----------

        shell : IPython shell

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

        knitr_hooks = """
        library(knitr)
        library(stringr)

        ke = environment(knit)
        render_ipynb = function (strict = FALSE) 
        {
            knit_hooks$restore()
            opts_chunk$set(dev = "png", highlight = FALSE)

            hook.s = function(x, options) {
                fn = paste(tempfile(), 'Rsource')
                of = file(fn, "w")
                writeChar(ke$indent_block(x), of)
                close(of)
                return(str_c('["text/plain","', fn, '"],'))
            }

            hook.s = function(x, options) {
                fn = paste(tempfile(), '.Rsource')
                of = file(fn, "w")
                writeChar(ke$indent_block(x), of)
                close(of)
                return(str_c('["text/plain","', fn, '"],'))
            }

            hook.e = function(x, options) {
                fn = paste(tempfile(), '.Rerror')
                of = file(fn, "w")
                writeChar(ke$indent_block(x), of)
                close(of)
                return(str_c('["text/plain","', fn, '"],'))
            }

            hook.o = function(x, options) {
                fn = paste(tempfile(), '.Routput')
                of = file(fn, "w")
                writeChar(ke$indent_block(x), of)
                close(of)
                return(str_c('["text/plain","', fn, '"],'))
            }

            hook.w = function(x, options) {
                fn = paste(tempfile(), '.Rwarning')
                of = file(fn, "w")
                writeChar(ke$indent_block(x), of)
                close(of)
                return(str_c('["text/plain","', fn, '"],'))
            }

            hook.m = function(x, options) {
                fn = paste(tempfile(), '.Rwarning')
                of = file(fn, "w")
                writeChar(ke$indent_block(x), of)
                close(of)
                return(str_c('["text/plain","', fn, '"],'))
            }

            knit_hooks$set(source = hook.s, output = hook.o, warning = hook.w,
                           error = hook.e, 
                message = hook.m, inline = function(x) sprintf(if (inherits(x, 
                    "AsIs")) 
                    "%s"
                else "`%s`", ke$.inline.hook(ke$format_sci(x, "html"))), plot = hook_plot_ipynb)
        }

        hook_plot_ipynb = function (x, options) 
        {
            base = opts_knit$get("base.url")
            if(is.null(base)) {
                base = ''
            }
            filename = sprintf("%s%s", base, ke$.upload.url(x));
            return(sprintf('["image/png","%s"],', filename))
        }

        render_ipynb()
        """
        old_writeconsole = ri.get_writeconsole()
        ri.set_writeconsole(self.write_console)
        ri.baseenv['eval'](ri.parse(knitr_hooks))
        ri.set_writeconsole(old_writeconsole)

    def eval(self, code, knitr_args={}):
        '''
        Parse and evaluate a code with rpy2.
        Returns the output to R's stdout() connection
        and the value of eval(parse(code)).
        '''
        code = code.strip()
        help_call = False
        if code.startswith('?') or code.startswith('help'):
            help_call = True

        old_writeconsole = ri.get_writeconsole()
        ri.set_writeconsole(self.write_console)

        try:
            with capture_output(True, False) as io:
                display_data = self.knitr(code, **knitr_args)
        except ri.RRuntimeError as exception:
            exception = str_to_unicode(str(exception))
            sys.stderr.write(str_to_unicode(str(exception)))
            display_data = {}

        for tag, data in display_data:
            # hack to catch messages when help(blah) fails
            # the return values from knitr only have one item in each dict
            value = data.values()[0]
            key = data.keys()[0]
            if ('plain' in key) and (("No documentation for" in value 
                and "specified packages" in value) or
                                     ("No vignettes or demos" in value 
                and "fuzzy matching" in value)):
                sys.stderr.write(value)
            else:
                publish_display_data(tag, data)

        if help_call:
            # help was called at the beginning of the code
            # write the output to page

            # it could be called more than once, but we only
            # print the first call, as subsequent calls would not
            # start the cell

            help = 'R Help' + io.stdout.split('R Help')[0]
            page(io.stdout)

        return '', ri.NULL

    def knitr(self, code, height=7, width=7, dpi=72):

        tmpd = tempfile.mkdtemp()

        Rmd_file = open("%s/code.Rmd" % tmpd, "w")
        md_filename = Rmd_file.name.replace("Rmd", "md")

        interpolator = {'height': height,
                        'width': width,
                        'dpi': dpi,
                        'path':tmpd,
                        'code':code.strip()}

        Rmd_file.write("""

``` {r fig.path="%(path)s", fig.height=%(height)d, fig.width=%(width)d, dpi=%(dpi)d}
%(code)s
```

        """ % interpolator)
        Rmd_file.close()
        ri.baseenv['eval'](ri.parse("library(knitr); knit('%s','%s')" % (Rmd_file.name, md_filename)))
        json_str = '[' + open(md_filename, 'r').read().strip()[:-1].replace('\n','\\n') + ']'
        md_output = json.loads(json_str)

        display_data = []

        for mime, fname in md_output:
            if os.path.splitext(fname)[1] != '.Rerror':
                data = open(fname).read().strip()
                os.remove(fname)
                if data:
                    display_data.append(('RMagic.R', {mime: data}))
            else:
                sys.stderr.write(open(fname).read())

        # kill the temporary directory
        rmtree(tmpd)

        return display_data

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
        '-w', '--width', type=int, default=7,
        help='Width of figure as "fig.width" sent to knitr.'
        )
    @argument(
        '-h', '--height', type=int, default=7,
        help='Height of figure as "fig.height" sent to knitr.'
        )
    @argument('--dpi', default=72,
              type=int,
              help='Argument "dpi" passed to knitr.'
              )
    @argument(
        '-d', '--dataframe', action='append',
        help='Convert these objects to data.frames and return as structured arrays.'
        )
    @argument(
        '-b', '--bg',
        help='Background of png plotting device sent as an argument to *png* in R.'
        )
    @argument(
        'code',
        nargs='*',
        )
    @needs_local_scope
    @line_cell_magic
    def R(self, line, cell=None, local_ns=None):
        '''
        Execute code in R, execute through knitr and pull some of the results back into the Python namespace.

        Multiple R lines can be executed by joining them with semicolons::

            In [4]: %R X=c(1,4,5,7); sd(X); mean(X)
                X = c(1, 4, 5, 7)

                sd(X)

                ## [1] 2.5

                mean(X)

                ## [1] 4.25

        As a cell, this will run a block of R code, without bringing anything back by default::

            In [10]: %%R
               ....: Y = c(2,4,3,9)
               ....: summary(lm(Y~X))
               ....: 
                Y = c(2, 4, 3, 9)
                summary(lm(Y ~ X))

                ## 
                ## Call:
                ## lm(formula = Y ~ X)
                ## 
                ## Residuals:
                ##     1     2     3     4 
                ##  0.88 -0.24 -2.28  1.64 
                ## 
                ## Coefficients:
                ##             Estimate Std. Error t value Pr(>|t|)
                ## (Intercept)    0.080      2.300    0.03     0.98
                ## X              1.040      0.482    2.16     0.16
                ## 
                ## Residual standard error: 2.09 on 2 degrees of freedom
                ## Multiple R-squared: 0.699,Adjusted R-squared: 0.549 
                ## F-statistic: 4.65 on 1 and 2 DF,  p-value: 0.164

        In the notebook, plots are published as the output of the cell.

        %R plot(X, Y)

        will create a scatter plot of X bs Y.

        If cell is not None and line has some R code, it is prepended to
        the R code in cell.

        Objects can be passed back and forth between rpy2 and python via the -i -o flags in line::

            In [13]: Z = np.array([1,4,5,10]) 

            In [14]: %R -i Z mean(Z)
                mean(Z)

                ## [1] 5

            In [15]: %R -o W W=Z*mean(Z) 
                W = Z * mean(Z)


            In [16]: W
            Out[16]: array([  5.,  20.,  25.,  50.])

        The --dataframe argument will attempt to return structured arrays. 
        This is useful for dataframes with
        mixed data types. Note also that for a data.frame, 
        if it is returned as an ndarray, it is transposed::

            In [18]: dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')]

            In [19]: datapy = np.array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c'), (4, 5, 'e')], dtype=dtype)

            In [21]: %%R -o datar -i datapy
            datar = datapy
               ....: 
                datar = datapy


            In [22]: datar
            Out[22]: 
            array([['1', '2', '3', '4'],
                   ['2', '3', '2', '5'],
                   ['a', 'b', 'c', 'e']], 
                  dtype='|S1')

            In [23]: %%R -d datar -i datapy
            datar = datapy
               ....: 
                datar = datapy


            In [24]: datar
            Out[24]: 
            array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c'), (4, 5.0, 'e')], 
                  dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')])

        The --dataframe argument first tries colnames, then names.
        If both are NULL, it returns an ndarray (i.e. unstructured)::

            In [1]: %R mydata=c(4,6,8.3)

            In [2]: %R -d mydata

            In [3]: mydata
            Out[3]: array([ 4. ,  6. ,  8.3])

            In [4]: %R names(mydata) = c('a','b','c')

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
                    val = self.shell.user_ns[input]
                self.r.assign(input, self.pyconverter(val))

        knitr_argdict = dict([(n, getattr(args, n)) for n in ['height', 'width', 'dpi']])

        text_output = ''
        if line_mode:
            for line in code.split(';'):
                text_result, result = self.eval(line, knitr_argdict)
                text_output += text_result
            if text_result:
                # the last line printed something to the console so we won't return it
                return_output = False
        else:
            text_result, result = self.eval(code, knitr_argdict)
            text_output += text_result

        # try to turn every output into a numpy array
        # this means that output are assumed to be castable
        # as numpy arrays

        if args.output:
            for output in ','.join(args.output).split(','):
                self.shell.push({output:self.Rconverter(self.r(output), dataframe=False)})

        if args.dataframe:
            for output in ','.join(args.dataframe).split(','):
                self.shell.push({output:self.Rconverter(self.r(output), dataframe=True)})

        # if in line mode and return_output, return the result as an ndarray
        return_output = False
        if return_output:
            if result != ri.NULL:
                return self.Rconverter(result, dataframe=False)

__doc__ = __doc__.format(
                R_DOC = ' '*8 + RMagics.R.__doc__,
                RPUSH_DOC = ' '*8 + RMagics.Rpush.__doc__,
                RPULL_DOC = ' '*8 + RMagics.Rpull.__doc__,
                RGET_DOC = ' '*8 + RMagics.Rget.__doc__
)




_loaded = False
def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(RMagics)
        _loaded = True
