"""ButtonWidget class.  

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
import base64

from .widget import Widget
from IPython.utils.traitlets import Unicode, Bytes

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ImageWidget(Widget):
    target_name = Unicode('ImageWidgetModel')
    default_view_name = Unicode('ImageView')
    
    # Define the custom state properties to sync with the front-end
    _keys = ['image_format', 'width', 'height', '_b64value']
    image_format = Unicode('png')
    width = Unicode()
    height = Unicode()
    _b64value = Unicode()
    
    value = Bytes()
    def _value_changed(self, name, old, new):
        self._b64value = base64.b64encode(new)