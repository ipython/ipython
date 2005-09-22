"""Module for interactive demos using IPython.

Sorry, but this uses Python 2.3 features, so it won't work in 2.2 environments.
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
from IPython.genutils import marquee, shlex_split

class DemoError(exceptions.Exception): pass

class Demo:
    def __init__(self,fname,arg_str='',mark_pause='# pause',
                 mark_silent='# silent',auto=False):
        """Make a new demo object.  To run the demo, simply call the object.

        Inputs:
        
          - fname = filename.

        Optional inputs:

          - arg_str(''): a string of arguments, internally converted to a list
          just like sys.argv, so the demo script can see a similar
          environment.

          - mark_pause ('# pause'), mark_silent('# silent'): marks for pausing
          (block boundaries) and to tag blocks as silent.  The marks are
          turned into regexps which match them as standalone in a line, with
          all leading/trailing whitespace ignored.

          - auto(False): flag to run each block automatically without
          confirmation.  Note that silent blocks are always automatically
          executed.  This flag is an attribute of the object, and can be
          changed at runtime simply by reassigning it.
          """

        self.fname = fname
        self.mark_pause = mark_pause
        self.re_pause = re.compile(r'^\s*%s\s*$' % mark_pause,re.MULTILINE)
        self.mark_silent = mark_silent
        self.re_silent = re.compile(r'^\s*%s\s*$' % mark_silent,re.MULTILINE)
        self.auto = auto
        self.sys_argv = [fname]+shlex_split(arg_str)

        # get a few things from ipython.  While it's a bit ugly design-wise,
        # it ensures that things like color scheme and the like are always in
        # sync with the ipython mode being used.  This class is only meant to
        # be used inside ipython anyways,  so it's OK.
        self.ip_showtraceback = __IPYTHON__.showtraceback
        self.ip_ns = __IPYTHON__.user_ns
        self.ip_colors = __IPYTHON__.rc['colors']

        # read data and parse into blocks
        fobj = file(fname,'r')
        self.src = fobj.read()
        fobj.close()
        self.src_blocks = [b.strip() for b in self.re_pause.split(self.src) if b]
        self.silent = [bool(self.re_silent.findall(b)) for b in self.src_blocks]
        self.nblocks = len(self.src_blocks)

        # try to colorize blocks
        colorize = Parser().format
        col_scheme = self.ip_colors
        self.src_blocks_colored = [colorize(s_blk,'str',col_scheme)
                                   for s_blk in self.src_blocks]

        # finish initialization
        self.reset()

    def reset(self):
        """Reset the namespace and seek pointer to restart the demo"""
        self.user_ns  = {}
        self.finished = False
        self.block_index = 0

    def again(self):
        """Repeat the last block"""
        self.block_index -= 1
        self()

    def _validate_index(self,index):
        if index<0 or index>=self.nblocks:
            raise ValueError('invalid block index %s' % index)

    def seek(self,index):
        """Move the current seek pointer to the given block"""
        self._validate_index(index)
        self.block_index = index-1
        self.finished = False

    def show_block(self,index=None):
        """Show a single block on screen"""
        if index is None:
            if self.finished:
                print 'Demo finished.  Use reset() if you want to rerun it.'
                return
            index = self.block_index
        else:
            self._validate_index(index)
        print marquee('<%s> block # %s (%s/%s)' %
                      (self.fname,index,index+1,self.nblocks))
        print self.src_blocks_colored[index],

    def show(self):
        """Show entire demo on screen, block by block"""

        fname = self.fname
        nblocks = self.nblocks
        silent = self.silent
        for index,block in enumerate(self.src_blocks_colored):
            if silent[index]:
                print marquee('<%s> SILENT block # %s (%s/%s)' %
                              (fname,index,index+1,nblocks))
            else:
                print marquee('<%s> block # %s (%s/%s)' %
                              (fname,index,index+1,nblocks))
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
            if self.silent[index]:
                print marquee('Executing silent block # %s (%s/%s)' %
                              (index,index+1,self.nblocks))
            else:
                self.show_block(index)
                if not self.auto:
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
            self.ip_showtraceback(filename=self.fname)
        else:
            self.ip_ns.update(self.user_ns)

        if self.block_index == self.nblocks:
            print
            print marquee(' END OF DEMO ')
            print marquee('Use reset() if you want to rerun it.')
            self.finished = True
