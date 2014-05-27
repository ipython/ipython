"""Utility for getting the system's node.js command."""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import warnings

from IPython.utils.process import get_output_error_code
from IPython.utils.version import check_version
from IPython.nbconvert.utils.exceptions import ConversionException

class NodeJSMissing(ConversionException):
    """Exception raised when node.js is missing."""
    pass


def get_node_cmd():
    """Gets the command to run node.

    Returns False if no valid command is available."""
    # prefer md2html via marked if node.js >= 0.9.12 is available
    # node is called nodejs on debian, so try that first
    node = 'nodejs'
    if not _verify_node(node):
        node = 'node'
        if not _verify_node(node):
            warnings.warn(  "Node.js 0.9.12 or later wasn't found.\n" +
                            "Nbconvert will try to use Pandoc instead.")
            return False
    return node

def _verify_node(cmd):
    """Verify that the node command exists and is at least the minimum supported
    version of node.

    Parameters
    ----------
    cmd : string
        Node command to verify (i.e 'node')."""
    try:
        out, err, return_code = get_output_error_code([cmd, '--version'])
    except OSError:
        # Command not found
        return False
    if return_code:
        # Command error
        return False
    return check_version(out.lstrip('v'), '0.9.12')
