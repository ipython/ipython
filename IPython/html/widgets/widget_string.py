"""StringWidget class.  

Represents a unicode string using a widget.
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
class StringWidget(Widget):
    target_name = Unicode('StringWidgetModel')
    default_view_name = Unicode('TextBoxView')

    # Keys
    _keys = ['value', 'disabled']
    value = Unicode(help="String value")
    disabled = Bool(False, help="Enable or disable user changes")
