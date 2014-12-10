"""Link and DirectionalLink classes.

Propagate changes between widgets on the javascript side
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2014, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from .widget import Widget
from IPython.utils.traitlets import Unicode, Tuple, Any

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

    # for compatibility with traitlet links
    def unlink(self):
        self.close()


def link(*args):
    return Link(widgets=args)


class DirectionalLink(Widget):
    """Directional Link Widget"""
    _model_name = Unicode('DirectionalLinkModel', sync=True)
    targets = Any(sync=True)
    source = Tuple(sync=True)

    # Does not quite behave like other widgets but reproduces
    # the behavior of IPython.utils.traitlets.directional_link
    def __init__(self, source, targets=(), **kwargs):
        kwargs['source'] = source
        kwargs['targets'] = targets
        super(DirectionalLink, self).__init__(**kwargs)

    # for compatibility with traitlet links
    def unlink(self):
        self.close()


def dlink(source, *targets):
    return DirectionalLink(source, targets)
