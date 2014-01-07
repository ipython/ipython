"""FloatWidget class.  

Represents an unbounded float using a widget.
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
from IPython.utils.traitlets import Unicode, Float, Bool, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class FloatWidget(DOMWidget):
    target_name = Unicode('FloatWidgetModel')
    default_view_name = Unicode('FloatTextView')

    # Keys
    keys = ['value', 'disabled', 'description'] + DOMWidget.keys
    value = Float(0.0, help="Float value") 
    disabled = Bool(False, help="Enable or disable user changes")
    description = Unicode(help="Description of the value this widget represents")
