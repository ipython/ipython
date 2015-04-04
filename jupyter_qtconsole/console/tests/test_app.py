"""Test QtConsoleApp"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import nose.tools as nt

from traitlets.tests.utils import check_help_all_output
from IPython.testing.decorators import skip_if_no_x11

@skip_if_no_x11
def test_help_output():
    """jupyter qtconsole --help-all works"""
    check_help_all_output('jupyter_qtconsole')

