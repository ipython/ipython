"""Tests for the key iplib module, where the main ipython class is defined.
"""

import nose.tools as nt


def test_reset():
    """reset must clear most namespaces."""
    ip = _ip.IP
    ip.reset()  # first, it should run without error
    # Then, check that most namespaces end up empty
    for ns in ip.ns_refs_table:
        if ns is ip.user_ns:
            # The user namespace is reset with some data, so we can't check for
            # it being empty
            continue
        nt.assert_equals(len(ns),0)
