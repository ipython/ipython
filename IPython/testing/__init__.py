"""Testing support (tools to test IPython itself).
"""

# User-level entry point for testing
def test():
    """Run the entire IPython test suite.

    For fine-grained control, you should use the :file:`iptest` script supplied
    with the IPython installation."""

    # Do the import internally, so that this function doesn't increase total
    # import time
    from iptest import run_iptestall
    run_iptestall()

# So nose doesn't try to run this as a test itself and we end up with an
# infinite test loop
test.__test__ = False
