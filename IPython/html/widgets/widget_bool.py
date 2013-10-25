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
from widget import Widget
from IPython.utils.traitlets import Unicode, Bool, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class BoolWidget(Widget):
    target_name = Unicode('BoolWidgetModel')
    default_view_name = Unicode('CheckboxView')

    # Model Keys
    _keys = ['value', 'description', 'disabled']
    value = Bool(False, help="Bool value")
    description = Unicode('', help="Description of the boolean (label).") 
    disabled = Bool(False, help="Enable or disable user changes.")
    