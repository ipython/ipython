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
from IPython.utils.traitlets import Unicode, Bool, List, Instance

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ContainerWidget(DOMWidget):
    view_name = Unicode('ContainerView', sync=True)

    # Keys, all private and managed by helper methods.  Flexible box model
    # classes...
    children = List(Instance(DOMWidget))
    _children = List(Instance(DOMWidget), sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self.on_trait_change(self._validate, ['children'])

    def _validate(self, name, old, new):
        """Validate children list.

        Makes sure only one instance of any given model can exist in the 
        children list.
        An excellent post on uniqifiers is available at 
            http://www.peterbe.com/plog/uniqifiers-benchmark
        which provides the inspiration for using this implementation.  Below
        I've implemented the `f5` algorithm using Python comprehensions."""
        if new is not None and isinstance(new, list):
            seen = {}
            def add_item(i):
                seen[i.model_id] = True
                return i
            return [add_item(i) for i in new if not i.model_id in seen]


class PopupWidget(ContainerWidget):
    view_name = Unicode('PopupView', sync=True)
    
    description = Unicode(sync=True)
    button_text = Unicode(sync=True)
