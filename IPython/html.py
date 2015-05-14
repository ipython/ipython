"""
Shim to maintain backwards compatibility with old IPython.html imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

warn("The `IPython.html` package has been deprecated. "
     "You should import from `notebook` instead. "
     "`IPython.html.widgets` has moved to `ipython_widgets`.")

from IPython.utils.shimmodule import ShimModule

_widgets = sys.modules['IPython.html.widgets'] = ShimModule(
    src='IPython.html.widgets', mirror='ipython_widgets')

_html = ShimModule(
    src='IPython.html', mirror='notebook')

# hook up widgets
_html.widgets = _widgets
sys.modules['IPython.html'] = _html

if __name__ == '__main__':
    from notebook import notebookapp as app
    app.launch_new_instance()
