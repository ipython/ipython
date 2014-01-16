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
from IPython.utils.traitlets import Unicode, Bool, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class CheckBoxWidget(DOMWidget):
    view_name = Unicode('CheckBoxView', sync=True)

    # Model Keys
    value = Bool(False, help="Bool value", sync=True)
    description = Unicode('', help="Description of the boolean (label).", sync=True) 
    disabled = Bool(False, help="Enable or disable user changes.", sync=True)


class ToggleButtonWidget(CheckBoxWidget):
    view_name = Unicode('ToggleButtonView', sync=True)
    