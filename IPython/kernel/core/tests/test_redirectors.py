# encoding: utf-8

"""
Test the output capture at the OS level, using file descriptors.
"""

__docformat__ = "restructuredtext en"

#---------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team                         
#                                                                           
#  Distributed under the terms of the BSD License.  The full license is in  
#  the file COPYING, distributed as part of this software.                  
#---------------------------------------------------------------------------
 

import os
from cStringIO import StringIO
import sys


def test_redirector():
    """ Checks that the redirector can be used to do synchronous capture.
    """
    # Flush the stdout, so as not to have side effects between
    # tests.
    sys.stdout.flush()
    sys.stderr.flush()
    from IPython.kernel.core.fd_redirector import FDRedirector
    r = FDRedirector()
    out = StringIO()
    try:
        r.start()
        for i in range(10):
            os.system('echo %ic' % i)
            print >>out, r.getvalue(),
            print >>out, i
    except:
        r.stop()
        raise
    r.stop()
    assert out.getvalue() == "".join("%ic\n%i\n" %(i, i) for i in range(10))
    sys.stdout.flush()
    sys.stderr.flush()


def test_redirector_output_trap():
    """ This test check not only that the redirector_output_trap does
        trap the output, but also that it does it in a gready way, that
        is by calling the callback ASAP.
    """
    # Flush the stdout, so as not to have side effects between
    # tests.
    sys.stdout.flush()
    sys.stderr.flush()
    from IPython.kernel.core.redirector_output_trap import RedirectorOutputTrap
    out = StringIO()
    trap = RedirectorOutputTrap(out.write, out.write)
    try:
        trap.set()
        for i in range(10):
            os.system('echo %ic' % i)
            print "%ip" % i
            print >>out, i
    except:
        trap.unset()
        raise
    trap.unset()
    sys.stdout.flush()
    sys.stderr.flush()
    assert out.getvalue() == "".join("%ic\n%ip\n%i\n" %(i, i, i) 
                                                    for i in range(10))



if __name__ == '__main__':
    print "Testing redirector...",
    test_redirector()
    test_redirector_output_trap()
    print "Done."

