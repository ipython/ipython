"""Container class.  

Represents a container that can be used to group other widgets.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Tuple, TraitError, Int, CaselessStrEnum
from IPython.utils.warn import DeprecatedClass

class Container(DOMWidget):
    """Displays multiple widgets in a group."""
    _view_name = Unicode('ContainerView', sync=True)

    # Child widgets in the container.
    # Using a tuple here to force reassignment to update the list.
    # When a proper notifying-list trait exists, that is what should be used here.
    children = Tuple(sync=True, allow_none=False)

    def __init__(self, children = (), **kwargs):
        kwargs['children'] = children
        super(Container, self).__init__(**kwargs)
        self.on_displayed(Container._fire_children_displayed)

    def _fire_children_displayed(self):
        for child in self.children:
            child._handle_displayed()


class Popup(Container):
    """Displays multiple widgets in an in page popup div."""
    _view_name = Unicode('PopupView', sync=True)
    
    description = Unicode(sync=True)
    button_text = Unicode(sync=True)


class FlexContainer(Container):
    """Displays multiple widgets using the flexible box model."""
    _view_name = Unicode('FlexContainerView', sync=True)
    orientation = CaselessStrEnum(values=['vertical', 'horizontal'], default_value='vertical', sync=True)
    flex = Int(0, sync=True, help="""Specify the flexible-ness of the model.""")
    def _flex_changed(self, name, old, new):
        new = min(max(0, new), 2)
        if self.flex != new:
            self.flex = new

    _locations = ['start', 'center', 'end', 'baseline', 'stretch']
    pack = CaselessStrEnum(
        values=_locations, 
        default_value='start', allow_none=False, sync=True)
    align = CaselessStrEnum(
        values=_locations, 
        default_value='start', allow_none=False, sync=True)


def VBox(*pargs, **kwargs):
    """Displays multiple widgets vertically using the flexible box model."""
    kwargs['orientation'] = 'vertical'
    return FlexContainer(*pargs, **kwargs)

def HBox(*pargs, **kwargs):
    """Displays multiple widgets horizontally using the flexible box model."""
    kwargs['orientation'] = 'horizontal'
    return FlexContainer(*pargs, **kwargs)


# Remove in IPython 4.0
ContainerWidget = DeprecatedClass(Container, 'ContainerWidget')
PopupWidget = DeprecatedClass(Popup, 'PopupWidget')

