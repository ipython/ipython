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
from .widget import DOMWidget, register
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

    def __init__(self, value=None, **kwargs):
        if value is not None:
            kwargs['value'] = value
        super(_Bool, self).__init__(**kwargs)

@register('IPython.Checkbox')
class Checkbox(_Bool):
    """Displays a boolean `value` in the form of a checkbox.

       Parameters
       ----------
       value : {True,False}
           value of the checkbox: True-checked, False-unchecked
       description : str
	   description displayed next to the checkbox
"""
    _view_name = Unicode('CheckboxView', sync=True)


@register('IPython.ToggleButton')
class ToggleButton(_Bool):
    """Displays a boolean `value` in the form of a toggle button.

       Parameters
       ----------
       value : {True,False}
           value of the toggle button: True-pressed, False-unpressed
       description : str
	   description displayed next to the button
       tooltip: str
           tooltip caption of the toggle button
       icon: str
           font-awesome icon name
"""
    
    _view_name = Unicode('ToggleButtonView', sync=True)
    tooltip = Unicode(help="Tooltip caption of the toggle button.", sync=True)
    icon = Unicode('', help= "Font-awesome icon.", sync=True)

    button_style = CaselessStrEnum(
        values=['primary', 'success', 'info', 'warning', 'danger', ''], 
        default_value='', allow_none=True, sync=True, help="""Use a
        predefined styling for the button.""")


# Remove in IPython 4.0
CheckboxWidget = DeprecatedClass(Checkbox, 'CheckboxWidget')
ToggleButtonWidget = DeprecatedClass(ToggleButton, 'ToggleButtonWidget')
