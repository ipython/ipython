"""Container class.  

Represents a container that can be used to group other widgets.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Tuple, TraitError, Int, CaselessStrEnum
from IPython.utils.warn import DeprecatedClass

class Container(DOMWidget):
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
    _view_name = Unicode('PopupView', sync=True)
    
    description = Unicode(sync=True)
    button_text = Unicode(sync=True)


class FlexContainer(Container):
    _view_name = Unicode('FlexContainerView', sync=True)
    orientation = Unicode('vertical', sync=True)
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


class VBox(FlexContainer):
    _view_name = Unicode('VBoxContainerView', sync=True)


class HBox(FlexContainer):
    _view_name = Unicode('HBoxContainerView', sync=True)

ContainerWidget = DeprecatedClass(Container, 'ContainerWidget')
PopupWidget = DeprecatedClass(Popup, 'PopupWidget')

