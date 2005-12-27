# -*- coding: utf-8 -*-
"""Class to trap stdout and stderr and log them separately.

$Id: OutputTrap.py 958 2005-12-27 23:17:51Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

import exceptions
import sys
from cStringIO import StringIO

class OutputTrapError(exceptions.Exception):
    """Exception for OutputTrap class."""

    def __init__(self,args=None):
        exceptions.Exception.__init__(self)
        self.args = args

class OutputTrap:

    """Class to trap standard output and standard error. They get logged in
    StringIO objects which are available as <instance>.out and
    <instance>.err. The class also offers summary methods which format this
    data a bit.

    A word of caution: because it blocks messages, using this class can make
    debugging very tricky. If you are having bizarre problems silently, try
    turning your output traps off for a while. You can call the constructor
    with the parameter debug=1 for these cases. This turns actual trapping
    off, but you can keep the rest of your code unchanged (this has already
    been a life saver).

    Example:

    # config: trapper with a line of dots as log separator (final '\\n' needed)
    config = OutputTrap('Config','Out ','Err ','.'*80+'\\n')

    # start trapping output
    config.trap_all()

    # now all output is logged ...
    # do stuff...

    # output back to normal:
    config.release_all()

    # print all that got logged:
    print config.summary()

    # print individual raw data:
    print config.out.getvalue()
    print config.err.getvalue()
    """

    def __init__(self,name='Generic Output Trap',
                 out_head='Standard Output. ',err_head='Standard Error. ',
                 sum_sep='\n',debug=0,trap_out=0,trap_err=0,
                 quiet_out=0,quiet_err=0):
        self.name = name
        self.out_head = out_head
        self.err_head = err_head
        self.sum_sep = sum_sep
        self.out = StringIO()
        self.err = StringIO()
        self.out_save = None
        self.err_save = None
        self.debug = debug
        self.quiet_out = quiet_out
        self.quiet_err = quiet_err
        if trap_out:
            self.trap_out()
        if trap_err:
            self.trap_err()

    def trap_out(self):
        """Trap and log stdout."""
        if sys.stdout is self.out:
            raise OutputTrapError,'You are already trapping stdout.'
        if not self.debug:
            self._out_save = sys.stdout
            sys.stdout = self.out

    def release_out(self):
        """Release stdout."""
        if not self.debug:
            if not sys.stdout is self.out:
                raise OutputTrapError,'You are not trapping stdout.'
            sys.stdout = self._out_save
            self.out_save = None

    def summary_out(self):
        """Return as a string the log from stdout."""
        out = self.out.getvalue()
        if out:
            if self.quiet_out:
                return out
            else:
                return self.out_head + 'Log by '+ self.name + ':\n' + out
        else:
            return ''

    def flush_out(self):
        """Flush the stdout log. All data held in the log is lost."""

        self.out.close()
        self.out = StringIO()

    def trap_err(self):
        """Trap and log stderr."""
        if sys.stderr is self.err:
            raise OutputTrapError,'You are already trapping stderr.'
        if not self.debug:
            self._err_save = sys.stderr
            sys.stderr = self.err

    def release_err(self):
        """Release stderr."""
        if not self.debug:
            if not sys.stderr is self.err:
                raise OutputTrapError,'You are not trapping stderr.'
            sys.stderr = self._err_save
            self.err_save = None

    def summary_err(self):
        """Return as a string the log from stderr."""
        err = self.err.getvalue()
        if err:
            if self.quiet_err:
                return err
            else:
                return self.err_head + 'Log by '+ self.name + ':\n' + err
        else:
            return ''

    def flush_err(self):
        """Flush the stdout log. All data held in the log is lost."""

        self.err.close()
        self.err = StringIO()

    def trap_all(self):
        """Trap and log both stdout and stderr.

        Cacthes and discards OutputTrapError exceptions raised."""
        try:
            self.trap_out()
        except OutputTrapError:
            pass
        try:
            self.trap_err()
        except OutputTrapError:
            pass

    def release_all(self):
        """Release both stdout and stderr.

        Cacthes and discards OutputTrapError exceptions raised."""
        try:
            self.release_out()
        except OutputTrapError:
            pass
        try:
            self.release_err()
        except OutputTrapError:
            pass
        
    def summary_all(self):
        """Return as a string the log from stdout and stderr, prepending a separator
        to each (defined in __init__ as sum_sep)."""
        sum = ''
        sout = self.summary_out()
        if sout:
            sum += self.sum_sep + sout
        serr = self.summary_err()
        if serr:
            sum += '\n'+self.sum_sep + serr
        return sum

    def flush_all(self):
        """Flush stdout and stderr"""
        self.flush_out()
        self.flush_err()

    # a few shorthands
    trap = trap_all
    release = release_all
    summary = summary_all
    flush = flush_all
# end OutputTrap


#****************************************************************************
# Module testing. Incomplete, I'm lazy...

def _test_all():

    """Module testing functions, activated when the module is called as a
    script (not imported)."""

    # Put tests for this module in here.
    # Define them as nested functions so they don't clobber the
    # pydoc-generated docs

    def _test_():
        name = ''
        print '#'*50+'\nRunning test for ' + name
        # ...
        print 'Finished test for '+ name +'\n'+'#'*50

    def _test_OutputTrap():
        trap = OutputTrap(name = 'Test Trap', sum_sep = '.'*50+'\n',
                          out_head = 'SOut. ', err_head = 'SErr. ')

        name = 'OutputTrap class'
        print '#'*50+'\nRunning test for ' + name
        print 'Trapping out'
        trap.trap_out()
        print >>sys.stdout, '>>stdout. stdout is trapped.'
        print >>sys.stderr, '>>stderr. stdout is trapped.'
        trap.release_out()
        print trap.summary_out()

        print 'Trapping err'
        trap.trap_err()
        print >>sys.stdout, '>>stdout. stderr is trapped.'
        print >>sys.stderr, '>>stderr. stderr is trapped.'
        trap.release_err()
        print trap.summary_err()

        print 'Trapping all (no flushing)'
        trap.trap_all()
        print >>sys.stdout, '>>stdout. stdout/err is trapped.'
        print >>sys.stderr, '>>stderr. stdout/err is trapped.'
        trap.release_all()
        print trap.summary_all()

        print 'Trapping all (flushing first)'
        trap.flush()
        trap.trap_all()
        print >>sys.stdout, '>>stdout. stdout/err is trapped.'
        print >>sys.stderr, '>>stderr. stdout/err is trapped.'
        trap.release_all()
        print trap.summary_all()
        print 'Finished test for '+ name +'\n'+'#'*50

    # call the actual tests here:
    _test_OutputTrap()


if __name__=="__main__":
    # _test_all() # XXX BROKEN.
    pass

#************************ end of file <OutputTrap.py> ************************
