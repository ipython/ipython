"""Module for interactive demos using IPython.

This module implements a single class, Demo, for running Python scripts
interactively in IPython for demonstrations.  With very simple markup (a few
tags in comments), you can control points where the script stops executing and
returns control to IPython.

The file is run in its own empty namespace (though you can pass it a string of
arguments as if in a command line environment, and it will see those as
sys.argv).  But at each stop, the global IPython namespace is updated with the
current internal demo namespace, so you can work interactively with the data
accumulated so far.

By default, each block of code is printed (with syntax highlighting) before
executing it and you have to confirm execution.  This is intended to show the
code to an audience first so you can discuss it, and only proceed with
execution once you agree.  There are a few tags which allow you to modify this
behavior.

The supported tags are:

# <demo> --- stop ---

  Defines block boundaries, the points where IPython stops execution of the
  file and returns to the interactive prompt.

# <demo> silent

  Make a block execute silently (and hence automatically).  Typically used in
  cases where you have some boilerplate or initialization code which you need
  executed but do not want to be seen in the demo.
  
# <demo> auto

  Make a block execute automatically, but still being printed.  Useful for
  simple code which does not warrant discussion, since it avoids the extra
  manual confirmation.

# <demo> auto_all

  This tag can _only_ be in the first block, and if given it overrides the
  individual auto tags to make the whole demo fully automatic (no block asks
  for confirmation).  It can also be given at creation time (or the attribute
  set later) to override what's in the file.

While _any_ python file can be run as a Demo instance, if there are no stop
tags the whole file will run in a single block (no different that calling
first %pycat and then %run).  The minimal markup to make this useful is to
place a set of stop tags; the other tags are only there to let you fine-tune
the execution.

This is probably best explained with the simple example file below.  You can
copy this into a file named ex_demo.py, and try running it via:

from IPython.demo import Demo
d = Demo('ex_demo.py')
d()  <--- Call the d object (omit the parens if you have autocall on).

Each time you call the demo object, it runs the next block.  The demo object
has a few useful methods for navigation, like again(), jump(), seek() and
back().  It can be reset for a new run via reset() or reloaded from disk (in
case you've edited the source) via reload().  See their docstrings below.

#################### EXAMPLE DEMO <ex_demo.py> ###############################
'''A simple interactive demo to illustrate the use of IPython's Demo class.'''

print 'Hello, welcome to an interactive IPython demo.'

# The mark below defines a block boundary, which is a point where IPython will
# stop execution and return to the interactive prompt.
# Note that in actual interactive execution, 
# <demo> --- stop ---

x = 1
y = 2

# <demo> --- stop ---

# the mark below makes this block as silent
# <demo> silent

print 'This is a silent block, which gets executed but not printed.'

# <demo> --- stop ---
# <demo> auto
print 'This is an automatic block.'
print 'It is executed without asking for confirmation, but printed.'
z = x+y

print 'z=',x

# <demo> --- stop ---
# This is just another normal block.
print 'z is now:', z

print 'bye!'
################### END EXAMPLE DEMO <ex_demo.py> ############################

WARNING: this module uses Python 2.3 features, so it won't work in 2.2
environments.
"""
#*****************************************************************************
#       Copyright (C) 2005 Fernando Perez. <Fernando.Perez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#
#*****************************************************************************

import sys
import exceptions
import re

from IPython.PyColorize import Parser
from IPython.genutils import marquee, shlex_split, file_read

__all__ = ['Demo','DemoError']

class DemoError(exceptions.Exception): pass

def re_mark(mark):
    return re.compile(r'^\s*#\s+<demo>\s+%s\s*$' % mark,re.MULTILINE)

class Demo:

    re_stop     = re_mark('---\s?stop\s?---')
    re_silent   = re_mark('silent')
    re_auto     = re_mark('auto')
    re_auto_all = re_mark('auto_all')

    def __init__(self,fname,arg_str='',auto_all=None):
        """Make a new demo object.  To run the demo, simply call the object.

        See the module docstring for full details and an example (you can use
        IPython.Demo? in IPython to see it).

        Inputs:
        
          - fname = filename.

        Optional inputs:

          - arg_str(''): a string of arguments, internally converted to a list
          just like sys.argv, so the demo script can see a similar
          environment.

          - auto_all(None): global flag to run all blocks automatically without
          confirmation.  This attribute overrides the block-level tags and
          applies to the whole demo.  It is an attribute of the object, and
          can be changed at runtime simply by reassigning it to a boolean
          value.
          """

        self.fname    = fname
        self.sys_argv = [fname] + shlex_split(arg_str)
        self.auto_all = auto_all
        
        # get a few things from ipython.  While it's a bit ugly design-wise,
        # it ensures that things like color scheme and the like are always in
        # sync with the ipython mode being used.  This class is only meant to
        # be used inside ipython anyways,  so it's OK.
        self.ip_showtb   = __IPYTHON__.showtraceback
        self.ip_ns       = __IPYTHON__.user_ns
        self.ip_colorize = __IPYTHON__.pycolorize

        # load user data and initialize data structures
        self.reload()

    def reload(self):
        """Reload source from disk and initialize state."""
        # read data and parse into blocks
        self.src     = file_read(self.fname)
        src_b        = [b.strip() for b in self.re_stop.split(self.src) if b]
        self._silent = [bool(self.re_silent.findall(b)) for b in src_b]
        self._auto   = [bool(self.re_auto.findall(b)) for b in src_b]

        # if auto_all is not given (def. None), we read it from the file
        if self.auto_all is None:
            self.auto_all = bool(self.re_auto_all.findall(src_b[0]))
        else:
            self.auto_all = bool(self.auto_all)

        # Clean the sources from all markup so it doesn't get displayed when
        # running the demo
        src_blocks = []
        auto_strip = lambda s: self.re_auto.sub('',s)
        for i,b in enumerate(src_b):
            if self._auto[i]:
                src_blocks.append(auto_strip(b))
            else:
                src_blocks.append(b)
        # remove the auto_all marker
        src_blocks[0] = self.re_auto_all.sub('',src_blocks[0])

        self.nblocks = len(src_blocks)
        self.src_blocks = src_blocks

        # also build syntax-highlighted source
        self.src_blocks_colored = map(self.ip_colorize,self.src_blocks)

        # ensure clean namespace and seek offset
        self.reset()

    def reset(self):
        """Reset the namespace and seek pointer to restart the demo"""
        self.user_ns     = {}
        self.finished    = False
        self.block_index = 0

    def _validate_index(self,index):
        if index<0 or index>=self.nblocks:
            raise ValueError('invalid block index %s' % index)

    def seek(self,index):
        """Move the current seek pointer to the given block"""
        self._validate_index(index)
        self.block_index = index
        self.finished = False

    def back(self,num=1):
        """Move the seek pointer back num blocks (default is 1)."""
        self.seek(self.block_index-num)

    def jump(self,num):
        """Jump a given number of blocks relative to the current one."""
        self.seek(self.block_index+num)

    def again(self):
        """Move the seek pointer back one block and re-execute."""
        self.back(1)
        self()

    def show(self,index=None):
        """Show a single block on screen"""
        if index is None:
            if self.finished:
                print 'Demo finished.  Use reset() if you want to rerun it.'
                return
            index = self.block_index
        else:
            self._validate_index(index)
        print marquee('<%s> block # %s (%s remaining)' %
                      (self.fname,index,self.nblocks-index-1))
        print self.src_blocks_colored[index],

    def show_all(self):
        """Show entire demo on screen, block by block"""

        fname = self.fname
        nblocks = self.nblocks
        silent = self._silent
        for index,block in enumerate(self.src_blocks_colored):
            if silent[index]:
                print marquee('<%s> SILENT block # %s (%s remaining)' %
                              (fname,index,nblocks-index-1))
            else:
                print marquee('<%s> block # %s (%s remaining)' %
                              (fname,index,nblocks-index-1))
            print block,
            
    def __call__(self,index=None):
        """run a block of the demo.

        If index is given, it should be an integer >=1 and <= nblocks.  This
        means that the calling convention is one off from typical Python
        lists.  The reason for the inconsistency is that the demo always
        prints 'Block n/N, and N is the total, so it would be very odd to use
        zero-indexing here."""

        if index is None and self.finished:
            print 'Demo finished.  Use reset() if you want to rerun it.'
            return
        if index is None:
            index = self.block_index
        self._validate_index(index)
        try:
            next_block = self.src_blocks[index]
            self.block_index += 1
            if self._silent[index]:
                print marquee('Executing silent block # %s (%s remaining)' %
                              (index,self.nblocks-index-1))
            else:
                self.show(index)
                if self.auto_all or self._auto[index]:
                    print marquee('output')
                else:
                    print marquee('Press <q> to quit, <Enter> to execute...'),
                    ans = raw_input().strip()
                    if ans:
                        print marquee('Block NOT executed')
                        return
            try:
                save_argv = sys.argv
                sys.argv = self.sys_argv
                exec next_block in self.user_ns
            finally:
                sys.argv = save_argv
            
        except:
            self.ip_showtb(filename=self.fname)
        else:
            self.ip_ns.update(self.user_ns)

        if self.block_index == self.nblocks:
            print
            print marquee(' END OF DEMO ')
            print marquee('Use reset() if you want to rerun it.')
            self.finished = True

