"""
Test the output capture at the OS level, using file descriptors.
"""

import os
from cStringIO import StringIO


def test_redirector():
    """ Checks that the redirector can be used to do synchronous capture.
    """
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


def test_redirector_output_trap():
    """ This test check not only that the redirector_output_trap does
        trap the output, but also that it does it in a gready way, that
        is by calling the callabck ASAP.
    """
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
    assert out.getvalue() == "".join("%ic\n%ip\n%i\n" %(i, i, i) 
                                                    for i in range(10))

    

