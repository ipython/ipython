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
from IPython import iplib

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

ip = _ip    # This is the ipapi instance
IP = ip.IP  # This is the actual IPython shell 'raw' object.

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def test_reset():
    """reset must clear most namespaces."""
    IP.reset()  # first, it should run without error
    # Then, check that most namespaces end up empty
    for ns in IP.ns_refs_table:
        if ns is IP.user_ns:
            # The user namespace is reset with some data, so we can't check for
            # it being empty
            continue
        nt.assert_equals(len(ns),0)


# make sure that user_setup can be run re-entrantly in 'install' mode.
def test_user_setup():
    # use a lambda to pass kwargs to the generator
    user_setup = lambda a,k: iplib.user_setup(*a,**k)
    kw = dict(mode='install',interactive=False)

    # Call the user setup and verify that the directory exists
    yield user_setup, (ip.options.ipythondir,''),kw
    yield os.path.isdir,ip.options.ipythondir

    # Now repeat the operation with a non-existent directory. Check both that
    # the call succeeds and that the directory is created.
    tmpdir = tempfile.mktemp(prefix='ipython-test-')
    try:
        yield user_setup, (tmpdir,''),kw
        yield os.path.isdir,tmpdir
    finally:
        # In this case, clean up the temp dir once done
        shutil.rmtree(tmpdir)
