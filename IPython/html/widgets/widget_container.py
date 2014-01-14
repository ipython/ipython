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
    target_name = Unicode('ContainerWidgetModel')
    view_name = Unicode('ContainerView')

    # Keys, all private and managed by helper methods.  Flexible box model
    # classes...
    keys = ['description', 'button_text', 'children'] + DOMWidget.keys # TODO: Use add/remove_class
    children = List(Instance(DOMWidget))
    
    description = Unicode()
    button_text = Unicode()
