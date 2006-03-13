# -*- coding: utf-8 -*-
"""Improved replacement for the Gnuplot.Gnuplot class.

This module imports Gnuplot and replaces some of its functionality with
improved versions. They add better handling of arrays for plotting and more
convenient PostScript generation, plus some fixes for hardcopy().

It also adds a convenient plot2 method for plotting dictionaries and
lists/tuples of arrays.

This module is meant to be used as a drop-in replacement to the original
Gnuplot, so it should be safe to do:

import IPython.Gnuplot2 as Gnuplot

$Id: Gnuplot2.py 1210 2006-03-13 01:19:31Z fperez $"""

import cStringIO
import os
import string
import sys
import tempfile
import time
import types

import Gnuplot as Gnuplot_ori
import Numeric

from IPython.genutils import popkey,xsys

# needed by hardcopy():
gp = Gnuplot_ori.gp

# Patch for Gnuplot.py 1.6 compatibility.
# Thanks to Hayden Callow <h.callow@elec.canterbury.ac.nz>
try:
    OptionException = Gnuplot_ori.PlotItems.OptionException
except AttributeError:
    OptionException = Gnuplot_ori.Errors.OptionError

# exhibit a similar interface to Gnuplot so it can be somewhat drop-in
Data      = Gnuplot_ori.Data
Func      = Gnuplot_ori.Func
GridData  = Gnuplot_ori.GridData
PlotItem  = Gnuplot_ori.PlotItem
PlotItems = Gnuplot_ori.PlotItems

# Modify some of Gnuplot's functions with improved versions (or bugfixed, in
# hardcopy's case). In order to preserve the docstrings at runtime, I've
# copied them from the original code.

# After some significant changes in v 1.7 of Gnuplot.py, we need to do a bit
# of version checking.

if Gnuplot_ori.__version__ <= '1.6':
    _BaseFileItem = PlotItems.File
    _BaseTempFileItem = PlotItems.TempFile

    # Fix the File class to add the 'index' option for Gnuplot versions < 1.7
    class File(_BaseFileItem):

        _option_list = _BaseFileItem._option_list.copy()
        _option_list.update({
            'index' : lambda self, index: self.set_option_index(index),
            })

        # A new initializer is needed b/c we want to add a modified
        # _option_sequence list which includes 'index' in the right place.
        def __init__(self,*args,**kw):
            self._option_sequence = ['binary', 'index', 'using', 'smooth', 'axes',
                         'title', 'with']

            _BaseFileItem.__init__(self,*args,**kw)

        # Let's fix the constructor docstring
        __newdoc = \
            """Additional Keyword arguments added by IPython:

             'index=<int>' -- similar to the `index` keyword in Gnuplot.
                 This allows only some of the datasets in a file to be
                 plotted. Datasets within a file are assumed to be separated
                 by _pairs_ of blank lines, and the first one is numbered as
                 0 (similar to C/Python usage)."""
        __init__.__doc__ = PlotItems.File.__init__.__doc__ + __newdoc

        def set_option_index(self, index):
            if index is None:
                self.clear_option('index')
            elif type(index) in [type(''), type(1)]:
                self._options['index'] = (index, 'index %s' % index)
            elif type(index) is type(()):
                self._options['index'] = (index,'index %s' %
                                          string.join(map(repr, index), ':'))
            else:
                raise OptionException('index=%s' % (index,))

    # We need a FileClass with a different name from 'File', which is a
    # factory function in 1.7, so that our String class can subclass FileClass
    # in any version.
    _FileClass = File

elif Gnuplot_ori.__version__ =='1.7':
    _FileClass = _BaseFileItem = PlotItems._FileItem
    _BaseTempFileItem = PlotItems._TempFileItem
    File = PlotItems.File

else:  # changes in the newer version (svn as of March'06)
     _FileClass = _BaseFileItem = PlotItems._FileItem
     _BaseTempFileItem = PlotItems._NewFileItem
     File = PlotItems.File


# Now, we can add our generic code which is version independent

# First some useful utilities
def eps_fix_bbox(fname):
    """Fix the bounding box of an eps file by running ps2eps on it.

    If its name ends in .eps, the original file is removed.

    This is particularly useful for plots made by Gnuplot with square aspect
    ratio: there is a bug in Gnuplot which makes it generate a bounding box
    which is far wider than the actual plot.

    This function assumes that ps2eps is installed in your system."""

    # note: ps2ps and eps2eps do NOT work, ONLY ps2eps works correctly. The
    # others make output with bitmapped fonts, which looks horrible.
    print 'Fixing eps file: <%s>' % fname
    xsys('ps2eps -f -q -l %s' % fname)
    if fname.endswith('.eps'):
        os.rename(fname+'.eps',fname)

def is_list1d(x,containers = [types.ListType,types.TupleType]):
    """Returns true if x appears to be a 1d list/tuple/array.

    The heuristics are: identify Numeric arrays, or lists/tuples whose first
    element is not itself a list/tuple. This way zipped lists should work like
    the original Gnuplot. There's no inexpensive way to know if a list doesn't
    have a composite object after its first element, so that kind of input
    will produce an error. But it should work well in most cases.
    """
    x_type = type(x)

    return x_type == Numeric.ArrayType and len(x.shape)==1 or \
           (x_type in containers and
            type(x[0]) not in containers + [Numeric.ArrayType])

def zip_items(items,titles=None):
    """zip together neighboring 1-d arrays, and zip standalone ones
    with their index. Leave other plot items alone."""

    class StandaloneItem(Exception): pass
    
    def get_titles(titles):
        """Return the next title and the input titles array.

        The input array may be changed to None when no titles are left to
        prevent extra unnecessary calls to this function."""
        
        try:
            title = titles[tit_ct[0]]  # tit_ct[0] is in zip_items'scope
        except IndexError:
            titles = None # so we don't enter again
            title = None
        else:
            tit_ct[0] += 1
        return title,titles

    new_items = []

    if titles:
        # Initialize counter. It was put in a list as a hack to allow the
        # nested get_titles to modify it without raising a NameError.
        tit_ct = [0]

    n = 0  # this loop needs to be done by hand
    while n < len(items):
        item = items[n]
        try:
            if is_list1d(item):
                if n==len(items)-1: # last in list
                    raise StandaloneItem
                else: # check the next item and zip together if needed
                    next_item = items[n+1]
                    if next_item is None:
                        n += 1
                        raise StandaloneItem
                    elif is_list1d(next_item):
                        # this would be best done with an iterator
                        if titles:
                            title,titles = get_titles(titles)
                        else:
                            title = None
                        new_items.append(Data(zip(item,next_item),
                                              title=title))
                        n += 1  # avoid double-inclusion of next item
                    else: # can't zip with next, zip with own index list
                        raise StandaloneItem
            else:  # not 1-d array
                new_items.append(item)
        except StandaloneItem:
            if titles:
                title,titles = get_titles(titles)
            else:
                title = None
            new_items.append(Data(zip(range(len(item)),item),title=title))
        except AttributeError:
            new_items.append(item)
        n+=1

    return new_items

# And some classes with enhanced functionality.
class String(_FileClass):
    """Make a PlotItem from data in a string with the same format as a File.

    This allows writing data directly inside python scripts using the exact
    same format and manipulation options which would be used for external
    files."""

    def __init__(self, data_str, **keyw):
        """Construct a String object.

        <data_str> is a string formatted exactly like a valid Gnuplot data
        file would be. All options from the File constructor are valid here.

        Warning: when used for interactive plotting in scripts which exit
        immediately, you may get an error because the temporary file used to
        hold the string data was deleted before Gnuplot had a chance to see
        it. You can work around this problem by putting a raw_input() call at
        the end of the script.

        This problem does not appear when generating PostScript output, only
        with Gnuplot windows."""

        self.tmpfile = _BaseTempFileItem()
        tmpfile = file(self.tmpfile.filename,'w')
        tmpfile.write(data_str)
        _BaseFileItem.__init__(self,self.tmpfile,**keyw)


class Gnuplot(Gnuplot_ori.Gnuplot):
    """Improved Gnuplot class.

    Enhancements: better plot,replot and hardcopy methods. New methods for
    quick range setting.
    """

    def xrange(self,min='*',max='*'):
        """Set xrange. If min/max is omitted, it is set to '*' (auto).

        Note that this is different from the regular Gnuplot behavior, where
        an unspecified limit means no change. Here any unspecified limit is
        set to autoscaling, allowing these functions to be used for full
        autoscaling when called with no arguments.

        To preserve one limit's current value while changing the other, an
        explicit '' argument must be given as the limit to be kept.

        Similar functions exist for [y{2}z{2}rtuv]range."""
        
        self('set xrange [%s:%s]' % (min,max))
             
    def yrange(self,min='*',max='*'):
        self('set yrange [%s:%s]' % (min,max))
             
    def zrange(self,min='*',max='*'):
        self('set zrange [%s:%s]' % (min,max))
             
    def x2range(self,min='*',max='*'):
        self('set xrange [%s:%s]' % (min,max))
             
    def y2range(self,min='*',max='*'):
        self('set yrange [%s:%s]' % (min,max))
             
    def z2range(self,min='*',max='*'):
        self('set zrange [%s:%s]' % (min,max))
             
    def rrange(self,min='*',max='*'):
        self('set rrange [%s:%s]' % (min,max))
             
    def trange(self,min='*',max='*'):
        self('set trange [%s:%s]' % (min,max))
             
    def urange(self,min='*',max='*'):
        self('set urange [%s:%s]' % (min,max))
             
    def vrange(self,min='*',max='*'):
        self('set vrange [%s:%s]' % (min,max))

    def set_ps(self,option):
        """Set an option for the PostScript terminal and reset default term."""

        self('set terminal postscript %s ' % option)
        self('set terminal %s' % gp.GnuplotOpts.default_term)

    def __plot_ps(self, plot_method,*items, **keyw):
        """Wrapper for plot/splot/replot, with processing of hardcopy options.

        For internal use only."""

        # Filter out PostScript options which will crash the normal plot/replot
        psargs = {'filename':None,
                  'mode':None,
                  'eps':None,
                  'enhanced':None,
                  'color':None,
                  'solid':None,
                  'duplexing':None,
                  'fontname':None,
                  'fontsize':None,
                  'debug':0 }

        for k in psargs.keys():
            if keyw.has_key(k):
                psargs[k] = keyw[k]
                del keyw[k]

        # Filter out other options the original plot doesn't know
        hardcopy = popkey(keyw,'hardcopy',psargs['filename'] is not None)
        titles = popkey(keyw,'titles',0)
        
        # the filename keyword should control hardcopy generation, this is an
        # override switch only which needs to be explicitly set to zero
        if hardcopy:
            if psargs['filename'] is None:
                raise ValueError, \
                      'If you request hardcopy, you must give a filename.'

            # set null output so nothing goes to screen. hardcopy() restores output
            self('set term dumb')
            # I don't know how to prevent screen output in Windows
            if os.name == 'posix':
                self('set output "/dev/null"')

        new_items = zip_items(items,titles)
        # plot_method is either plot or replot from the original Gnuplot class:
        plot_method(self,*new_items,**keyw)

        # Do hardcopy if requested
        if hardcopy:
            if psargs['filename'].endswith('.eps'):
                psargs['eps'] = 1
            self.hardcopy(**psargs)

    def plot(self, *items, **keyw):
        """Draw a new plot.

        Clear the current plot and create a new 2-d plot containing
        the specified items.  Each arguments should be of the
        following types:

        'PlotItem' (e.g., 'Data', 'File', 'Func') -- This is the most
            flexible way to call plot because the PlotItems can
            contain suboptions.  Moreover, PlotItems can be saved to
            variables so that their lifetime is longer than one plot
            command; thus they can be replotted with minimal overhead.

        'string' (e.g., 'sin(x)') -- The string is interpreted as
            'Func(string)' (a function that is computed by gnuplot).

        Anything else -- The object, which should be convertible to an
            array, is passed to the 'Data' constructor, and thus
            plotted as data.  If the conversion fails, an exception is
            raised.


        This is a modified version of plot(). Compared to the original in
        Gnuplot.py, this version has several enhancements, listed below.


        Modifications to the input arguments
        ------------------------------------

        (1-d array means Numeric array, list or tuple):

        (i) Any 1-d array which is NOT followed by another 1-d array, is
        automatically zipped with range(len(array_1d)). Typing g.plot(y) will
        plot y against its indices.

        (ii) If two 1-d arrays are contiguous in the argument list, they are
        automatically zipped together. So g.plot(x,y) plots y vs. x, and
        g.plot(x1,y1,x2,y2) plots y1 vs. x1 and y2 vs. x2.

        (iii) Any 1-d array which is followed by None is automatically zipped
        with range(len(array_1d)). In this form, typing g.plot(y1,None,y2)
        will plot both y1 and y2 against their respective indices (and NOT
        versus one another). The None prevents zipping y1 and y2 together, and
        since y2 is unpaired it is automatically zipped to its indices by (i)

        (iv) Any other arguments which don't match these cases are left alone and
        passed to the code below.

        For lists or tuples, the heuristics used to determine whether they are
        in fact 1-d is fairly simplistic: their first element is checked, and
        if it is not a list or tuple itself, it is assumed that the whole
        object is one-dimensional.

        An additional optional keyword 'titles' has been added: it must be a
        list of strings to be used as labels for the individual plots which
        are NOT PlotItem objects (since those objects carry their own labels
        within).


        PostScript generation
        ---------------------

        This version of plot() also handles automatically the production of
        PostScript output. The main options are (given as keyword arguments):

        - filename: a string, typically ending in .eps. If given, the plot is
        sent to this file in PostScript format.
        
        - hardcopy: this can be set to 0 to override 'filename'. It does not
        need to be given to produce PostScript, its purpose is to allow
        switching PostScript output off globally in scripts without having to
        manually change 'filename' values in multiple calls.

        All other keywords accepted by Gnuplot.hardcopy() are transparently
        passed, and safely ignored if output is sent to the screen instead of
        PostScript.

        For example:
        
        In [1]: x=frange(0,2*pi,npts=100)

        Generate a plot in file 'sin.eps':

        In [2]: plot(x,sin(x),filename = 'sin.eps')

        Plot to screen instead, without having to change the filename:

        In [3]: plot(x,sin(x),filename = 'sin.eps',hardcopy=0)

        Pass the 'color=0' option to hardcopy for monochrome output:

        In [4]: plot(x,sin(x),filename = 'sin.eps',color=0)

        PostScript generation through plot() is useful mainly for scripting
        uses where you are not interested in interactive plotting. For
        interactive use, the hardcopy() function is typically more convenient:
        
        In [5]: plot(x,sin(x))

        In [6]: hardcopy('sin.eps')  """
        
        self.__plot_ps(Gnuplot_ori.Gnuplot.plot,*items,**keyw)
        
    def plot2(self,arg,**kw):
        """Plot the entries of a dictionary or a list/tuple of arrays.        
        
        This simple utility calls plot() with a list of Gnuplot.Data objects
        constructed either from the values of the input dictionary, or the entries
        in it if it is a tuple or list.  Each item gets labeled with the key/index
        in the Gnuplot legend.

        Each item is plotted by zipping it with a list of its indices.

        Any keywords are passed directly to plot()."""

        if hasattr(arg,'keys'):
            keys = arg.keys()
            keys.sort()
        else:
            keys = range(len(arg))

        pitems = [Data(zip(range(len(arg[k])),arg[k]),title=`k`) for k in keys]
        self.plot(*pitems,**kw)

    def splot(self, *items, **keyw):
        """Draw a new three-dimensional plot.

        Clear the current plot and create a new 3-d plot containing
        the specified items.  Arguments can be of the following types:

        'PlotItem' (e.g., 'Data', 'File', 'Func', 'GridData' ) -- This
            is the most flexible way to call plot because the
            PlotItems can contain suboptions.  Moreover, PlotItems can
            be saved to variables so that their lifetime is longer
            than one plot command--thus they can be replotted with
            minimal overhead.

        'string' (e.g., 'sin(x*y)') -- The string is interpreted as a
            'Func()' (a function that is computed by gnuplot).

        Anything else -- The object is converted to a Data() item, and
            thus plotted as data.  Note that each data point should
            normally have at least three values associated with it
            (i.e., x, y, and z).  If the conversion fails, an
            exception is raised.

        This is a modified version of splot(). Compared to the original in
        Gnuplot.py, this version has several enhancements, listed in the
        plot() documentation.
        """
        
        self.__plot_ps(Gnuplot_ori.Gnuplot.splot,*items,**keyw)

    def replot(self, *items, **keyw):
        """Replot the data, possibly adding new 'PlotItem's.

        Replot the existing graph, using the items in the current
        itemlist.  If arguments are specified, they are interpreted as
        additional items to be plotted alongside the existing items on
        the same graph.  See 'plot' for details.

        If you want to replot to a postscript file, you MUST give the
        'filename' keyword argument in each call to replot. The Gnuplot python
        interface has no way of knowing that your previous call to
        Gnuplot.plot() was meant for PostScript output."""
        
        self.__plot_ps(Gnuplot_ori.Gnuplot.replot,*items,**keyw)

    # The original hardcopy has a bug. See fix at the end. The rest of the code
    # was lifted verbatim from the original, so that people using IPython get the
    # benefits without having to manually patch Gnuplot.py
    def hardcopy(self, filename=None,
                 mode=None,
                 eps=None,
                 enhanced=None,
                 color=None,
                 solid=None,
                 duplexing=None,
                 fontname=None,
                 fontsize=None,
                 debug = 0,
                 ):
        """Create a hardcopy of the current plot.

        Create a postscript hardcopy of the current plot to the
        default printer (if configured) or to the specified filename.

        Note that gnuplot remembers the postscript suboptions across
        terminal changes.  Therefore if you set, for example, color=1
        for one hardcopy then the next hardcopy will also be color
        unless you explicitly choose color=0.  Alternately you can
        force all of the options to their defaults by setting
        mode='default'.  I consider this to be a bug in gnuplot.

        Keyword arguments:

          'filename=<string>' -- if a filename is specified, save the
              output in that file; otherwise print it immediately
              using the 'default_lpr' configuration option.  If the
              filename ends in '.eps', EPS mode is automatically
              selected (like manually specifying eps=1 or mode='eps').

          'mode=<string>' -- set the postscript submode ('landscape',
              'portrait', 'eps', or 'default').  The default is
              to leave this option unspecified.

          'eps=<bool>' -- shorthand for 'mode="eps"'; asks gnuplot to
              generate encapsulated postscript.

          'enhanced=<bool>' -- if set (the default), then generate
              enhanced postscript, which allows extra features like
              font-switching, superscripts, and subscripts in axis
              labels.  (Some old gnuplot versions do not support
              enhanced postscript; if this is the case set
              gp.GnuplotOpts.prefer_enhanced_postscript=None.)

          'color=<bool>' -- if set, create a plot with color.  Default
              is to leave this option unchanged.

          'solid=<bool>' -- if set, force lines to be solid (i.e., not
              dashed).

          'duplexing=<string>' -- set duplexing option ('defaultplex',
              'simplex', or 'duplex').  Only request double-sided
              printing if your printer can handle it.  Actually this
              option is probably meaningless since hardcopy() can only
              print a single plot at a time.

          'fontname=<string>' -- set the default font to <string>,
              which must be a valid postscript font.  The default is
              to leave this option unspecified.

          'fontsize=<double>' -- set the default font size, in
              postscript points.

          'debug=<bool>' -- print extra debugging information (useful if
              your PostScript files are misteriously not being created).
        """

        if filename is None:
            assert gp.GnuplotOpts.default_lpr is not None, \
                   OptionException('default_lpr is not set, so you can only '
                                   'print to a file.')
            filename = gp.GnuplotOpts.default_lpr
            lpr_output = 1
        else:
            if filename.endswith('.eps'):
                eps = 1
            lpr_output = 0

        # Be careful processing the options.  If the user didn't
        # request an option explicitly, do not specify it on the 'set
        # terminal' line (don't even specify the default value for the
        # option).  This is to avoid confusing older versions of
        # gnuplot that do not support all of these options.  The
        # exception is 'enhanced', which is just too useful to have to
        # specify each time!

        setterm = ['set', 'terminal', 'postscript']
        if eps:
            assert mode is None or mode=='eps', \
                   OptionException('eps option and mode are incompatible')
            setterm.append('eps')
        else:
            if mode is not None:
                assert mode in ['landscape', 'portrait', 'eps', 'default'], \
                       OptionException('illegal mode "%s"' % mode)
                setterm.append(mode)
        if enhanced is None:
            enhanced = gp.GnuplotOpts.prefer_enhanced_postscript
        if enhanced is not None:
            if enhanced: setterm.append('enhanced')
            else: setterm.append('noenhanced')
        if color is not None:
            if color: setterm.append('color')
            else: setterm.append('monochrome')
        if solid is not None:
            if solid: setterm.append('solid')
            else: setterm.append('dashed')
        if duplexing is not None:
            assert duplexing in ['defaultplex', 'simplex', 'duplex'], \
                   OptionException('illegal duplexing mode "%s"' % duplexing)
            setterm.append(duplexing)
        if fontname is not None:
            setterm.append('"%s"' % fontname)
        if fontsize is not None:
            setterm.append('%s' % fontsize)

        self(string.join(setterm))
        self.set_string('output', filename)
        # replot the current figure (to the printer):
        self.refresh()

        # fperez. Ugly kludge: often for some reason the file is NOT created
        # and we must reissue the creation commands. I have no idea why!
        if not lpr_output:
            #print 'Hardcopy <%s>' % filename  # dbg
            maxtries = 20
            delay = 0.1  # delay (in seconds) between print attempts
            for i in range(maxtries):
                time.sleep(0.05)  # safety, very small delay
                if os.path.isfile(filename):
                    if debug:
                        print 'Hardcopy to file <%s> success at attempt #%s.' \
                        % (filename,i+1)
                    break
                time.sleep(delay)
                # try again, issue all commands just in case
                self(string.join(setterm))
                self.set_string('output', filename)
                self.refresh()
            if not os.path.isfile(filename):
                print >> sys.stderr,'ERROR: Tried %s times and failed to '\
                'create hardcopy file `%s`' % (maxtries,filename)

        # reset the terminal to its `default' setting:
        self('set terminal %s' % gp.GnuplotOpts.default_term)
        self.set_string('output')

#********************** End of file <Gnuplot2.py> ************************
