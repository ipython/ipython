"""Link and DirectionalLink classes.

Represents a button in the frontend using a widget.  Allows user to listen for
click events on the button and trigger backend code when the clicks are fired.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from .widget import Widget
from IPython.utils.traitlets import Unicode, Tuple

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


class Link(Widget):
    """Link Widget"""
    _model_name = Unicode('LinkModel', sync=True)
    widgets = Tuple(sync=True, allow_none=False)

    def __init__(self, widgets=(), **kwargs):
        kwargs['widgets'] = widgets
        super(Link, self).__init__(**kwargs)

def link(*args):
    return Link(widgets=args)
