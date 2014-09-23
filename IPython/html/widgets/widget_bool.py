"""Bool class.  

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
from IPython.utils.traitlets import Unicode, Bool, CaselessStrEnum
from IPython.utils.warn import DeprecatedClass

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _Bool(DOMWidget):
    """A base class for creating widgets that represent booleans."""
    value = Bool(False, help="Bool value", sync=True)
    description = Unicode('', help="Description of the boolean (label).", sync=True)
    disabled = Bool(False, help="Enable or disable user changes.", sync=True)


class Checkbox(_Bool):
    """Displays a boolean `value`."""
    _view_name = Unicode('CheckboxView', sync=True)


class ToggleButton(_Bool):
    """Displays a boolean `value`."""
    
    _view_name = Unicode('ToggleButtonView', sync=True)

    button_style = CaselessStrEnum(
        values=['primary', 'success', 'info', 'warning', 'danger', ''], 
        default_value='', allow_none=True, sync=True, help="""Use a
        predefined styling for the button.""")


# Remove in IPython 4.0
CheckboxWidget = DeprecatedClass(Checkbox, 'CheckboxWidget')
ToggleButtonWidget = DeprecatedClass(ToggleButton, 'ToggleButtonWidget')
