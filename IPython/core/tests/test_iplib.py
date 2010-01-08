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
from IPython.testing import decorators as dec

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

@dec.parametric
def test_reset():
    """reset must clear most namespaces."""
    # The number of variables in the private user_config_ns is not zero, but it
    # should be constant regardless of what we do
    nvars_config_ns = len(ip.user_config_ns)

    # Check that reset runs without error
    ip.reset()

    # Once we've reset it (to clear of any junk that might have been there from
    # other tests, we can count how many variables are in the user's namespace
    nvars_user_ns = len(ip.user_ns)

    # Now add a few variables to user_ns, and check that reset clears them
    ip.user_ns['x'] = 1
    ip.user_ns['y'] = 1
    ip.reset()
    
    # Finally, check that all namespaces have only as many variables as we
    # expect to find in them:
    for ns in ip.ns_refs_table:
        if ns is ip.user_ns:
            nvars_expected = nvars_user_ns
        elif ns is ip.user_config_ns:
            nvars_expected = nvars_config_ns
        else:
            nvars_expected = 0
            
        yield nt.assert_equals(len(ns), nvars_expected)
