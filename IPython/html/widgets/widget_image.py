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

from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, CUnicode, Bytes

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class ImageWidget(DOMWidget):
    _view_name = Unicode('ImageView', sync=True)
    
    # Define the custom state properties to sync with the front-end
    format = Unicode('png', sync=True)
    width = CUnicode(sync=True)
    height = CUnicode(sync=True)
    _b64value = Unicode(sync=True)
    
    value = Bytes()
    def _value_changed(self, name, old, new):
        self._b64value = base64.b64encode(new)