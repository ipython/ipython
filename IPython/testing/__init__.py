"""Testing support (tools to test IPython itself).
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2009-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

# User-level entry point for testing
def test(all=False):
    """Run the entire IPython test suite.

    For fine-grained control, you should use the :file:`iptest` script supplied
    with the IPython installation."""

    # Do the import internally, so that this function doesn't increase total
    # import time
    from iptest import run_iptestall
    run_iptestall(inc_slow=all)

# So nose doesn't try to run this as a test itself and we end up with an
# infinite test loop
test.__test__ = False
