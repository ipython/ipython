"""
Shim to maintain backwards compatibility with old IPython.html imports.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
from warnings import warn

warn("The `IPython.html` package has been deprecated. "
     "You should import from jupyter_notebook instead.")

from IPython.utils.shimmodule import ShimModule

sys.modules['IPython.html'] = ShimModule(
    src='IPython.html', mirror='jupyter_notebook')

if __name__ == '__main__':
    from jupyter_notebook import notebookapp as app
    app.launch_new_instance()
