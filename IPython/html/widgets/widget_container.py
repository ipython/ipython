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
from IPython.utils.traitlets import Unicode, Tuple, Instance, TraitError

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class TupleOfDOMWidgets(Tuple):
    """Like Tuple(Instance(DOMWidget)), but without checking length."""
    def validate_elements(self, obj, value):
        for v in value:
            if not isinstance(v, DOMWidget):
                raise TraitError("Container.children must be DOMWidgets, not %r" % v)
        return value

class ContainerWidget(DOMWidget):
    _view_name = Unicode('ContainerView', sync=True)

    # Keys, all private and managed by helper methods.  Flexible box model
    # classes...
    children = TupleOfDOMWidgets()
    _children = TupleOfDOMWidgets(sync=True)

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
