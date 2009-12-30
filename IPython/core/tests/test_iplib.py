"""Tests for the key iplib module, where the main ipython class is defined.
"""
#-----------------------------------------------------------------------------
# Module imports
#-----------------------------------------------------------------------------

# stdlib
import os
import shutil
import tempfile

# third party
import nose.tools as nt

# our own packages
from IPython.core import iplib
from IPython.core import ipapi


#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# Useful global ipapi object and main IPython one.  Unfortunately we have a
# long precedent of carrying the 'ipapi' global object which is injected into
# the system namespace as _ip, but that keeps a pointer to the actual IPython
# InteractiveShell instance, which is named IP.  Since in testing we do need
# access to the real thing (we want to probe beyond what ipapi exposes), make
# here a global reference to each.  In general, things that are exposed by the
# ipapi instance should be read from there, but we also will often need to use
# the actual IPython one.

# Get the public instance of IPython, and if it's None, make one so we can use
# it for testing
ip = ipapi.get()
if ip is None:
    # IPython not running yet,  make one from the testing machinery for
    # consistency when the test suite is being run via iptest
    from IPython.testing.plugin import ipdoctest
    ip = ipapi.get()

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test_reset():
    """reset must clear most namespaces."""
    ip.reset()  # first, it should run without error
    # Then, check that most namespaces end up empty
    for ns in ip.ns_refs_table:
        if ns is ip.user_ns:
            # The user namespace is reset with some data, so we can't check for
            # it being empty
            continue
        nt.assert_equals(len(ns),0)

    