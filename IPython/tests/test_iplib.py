"""Tests for the key iplib module, where the main ipython class is defined.
"""

import nose.tools as nt

# Useful global ipapi object and main IPython one
ip = _ip
IP = ip.IP


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


def test_user_setup():
    """make sure that user_setup can be run re-entrantly in 'install' mode.
    """
    # This should basically run without errors or output.
    IP.user_setup(ip.options.ipythondir,'','install')
