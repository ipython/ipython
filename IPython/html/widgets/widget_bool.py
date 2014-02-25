"""BoolWidget class.  

Represents a boolean using a widget.
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
from IPython.utils.traitlets import Unicode, Bool

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _BoolWidget(DOMWidget):
    value = Bool(False, help="Bool value", sync=True)
    description = Unicode('', help="Description of the boolean (label).", sync=True) 
    disabled = Bool(False, help="Enable or disable user changes.", sync=True)


class CheckboxWidget(_BoolWidget):
    _view_name = Unicode('CheckboxView', sync=True)


class ToggleButtonWidget(_BoolWidget):
    _view_name = Unicode('ToggleButtonView', sync=True)
    