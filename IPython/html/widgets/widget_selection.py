"""SelectionWidget class.  

Represents an enumeration using a widget.
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
from IPython.utils.traitlets import Unicode, List, Bool

#-----------------------------------------------------------------------------
# SelectionWidget
#-----------------------------------------------------------------------------
class SelectionWidget(DOMWidget):
    target_name = Unicode('SelectionWidgetModel')
    view_name = Unicode('DropdownView')

    # Keys
    keys = ['value', 'values', 'disabled', 'description'] + DOMWidget.keys
    value = Unicode(help="Selected value") # TODO: Any support
    values = List(help="List of values the user can select")
    disabled = Bool(False, help="Enable or disable user changes")
    description = Unicode(help="Description of the value this widget represents")
 