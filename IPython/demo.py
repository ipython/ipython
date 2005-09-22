"""Module for interactive demos using IPython.
"""
#*****************************************************************************
#       Copyright (C) 2005 Fernando Perez. <Fernando.Perez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#
#*****************************************************************************

import exceptions

from IPython.PyColorize import Parser
from IPython.genutils import marquee

class DemoError(exceptions.Exception): pass

class Demo:
    def __init__(self,fname,pause_mark='# pause',auto=False):

        self.fname = fname
        self.pause_mark = pause_mark
        self.auto = auto

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
        self.src_blocks = [b.strip() for b in self.src.split(pause_mark) if b]
        self.nblocks = len(self.src_blocks)

        # try to colorize blocks
        colorize = Parser().format
        col_scheme = self.ip_colors
        self.src_blocks_colored = [colorize(s_blk,'str',col_scheme)
                                   for s_blk in self.src_blocks]

        # finish initialization
        self.reset()

    def reset(self):
        self.user_ns  = {}
        self.finished = False
        self.block_index = 0

    def again(self):
        self.block_index -= 1
        self()


    def _validate_index(self,index):
        if index<0 or index>=self.nblocks:
            raise ValueError('invalid block index %s' % index)

    def seek(self,index):
        self._validate_index(index)
        self.block_index = index-1
        self.finished = False

    def show(self,index=None):
        if index is None:
            index = self.block_index
        else:
            self._validate_index(index)
        print marquee('<%s> block # %s (%s/%s)' %
                      (self.fname,index,index+1,self.nblocks))
        print self.src_blocks_colored[index],
        
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
            self.show(index)
            if not self.auto:
                print marquee('Press <q> to quit, <Enter> to execute...'),
                ans = raw_input().strip()
                if ans:
                    print marquee('Block NOT executed')
                    return
            
            exec next_block in self.user_ns
            
        except:
            self.ip_showtraceback(filename=self.fname)
        else:
            self.ip_ns.update(self.user_ns)

        if self.block_index == self.nblocks:
            print
            print marquee(' END OF DEMO ')
            print marquee('Use reset() if you want to rerun it.')
            self.finished = True

