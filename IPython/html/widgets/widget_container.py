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
    children = List(Instance(DOMWidget), sync=True)
    
    description = Unicode(sync=True)
    button_text = Unicode(sync=True)
