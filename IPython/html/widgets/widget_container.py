"""ContainerWidget class.  

Represents a container that can be used to group other widgets.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Tuple, TraitError

class ContainerWidget(DOMWidget):
    _view_name = Unicode('ContainerView', sync=True)

    # Child widgets in the container.
    # Using a tuple here to force reassignment to update the list.
    # When a proper notifying-list trait exists, that is what should be used here.
    children = Tuple(sync=True, allow_none=False)

    def __init__(self, children = (), **kwargs):
        kwargs['children'] = children
        super(ContainerWidget, self).__init__(**kwargs)
        self.on_displayed(ContainerWidget._fire_children_displayed)

    def _fire_children_displayed(self):
        for child in self.children:
            child._handle_displayed()


class PopupWidget(ContainerWidget):
    _view_name = Unicode('PopupView', sync=True)
    
    description = Unicode(sync=True)
    button_text = Unicode(sync=True)
