"""ContainerWidget class.  

Represents a container that can be used to group other widgets.
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
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Tuple, TraitError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class ContainerWidget(DOMWidget):
    _view_name = Unicode('ContainerView', sync=True)

    # Child widgets in the container.
    # Using a tuple here to force reassignment to update the list.
    # When a proper notifying-list trait exists, that is what should be used here.
    children = Tuple()
    _children = Tuple(sync=True)


    def __init__(self, **kwargs):
        super(ContainerWidget, self).__init__(**kwargs)
        self.on_displayed(ContainerWidget._fire_children_displayed)

    def _fire_children_displayed(self):
        for child in self._children:
            child._handle_displayed()

    def _children_changed(self, name, old, new):
        """Validate children list.

        Makes sure only one instance of any given model can exist in the 
        children list.
        An excellent post on uniqifiers is available at 
            http://www.peterbe.com/plog/uniqifiers-benchmark
        which provides the inspiration for using this implementation.  Below
        I've implemented the `f5` algorithm using Python comprehensions."""
        if new is not None:
            seen = {}
            def add_item(i):
                seen[i.model_id] = True
                return i
            self._children = [add_item(i) for i in new if not i.model_id in seen]


class PopupWidget(ContainerWidget):
    _view_name = Unicode('PopupView', sync=True)
    
    description = Unicode(sync=True)
    button_text = Unicode(sync=True)
