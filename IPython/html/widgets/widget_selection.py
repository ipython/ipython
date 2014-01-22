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
class _SelectionWidget(DOMWidget):
    value = Unicode(help="Selected value", sync=True) # TODO: Any support
    values = List(help="List of values the user can select", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)


class ToggleButtonsWidget(_SelectionWidget):
    view_name = Unicode('ToggleButtonsView', sync=True)


class DropdownWidget(_SelectionWidget):
    view_name = Unicode('DropdownView', sync=True)


class RadioButtonsWidget(_SelectionWidget):
    view_name = Unicode('RadioButtonsView', sync=True)
    

class ListBoxWidget(_SelectionWidget):
    view_name = Unicode('ListBoxView', sync=True)
