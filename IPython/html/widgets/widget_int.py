"""IntWidget class.  

Represents an unbounded int using a widget.
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
from IPython.utils.traitlets import Unicode, Int, Bool, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class IntWidget(Widget):
    target_name = Unicode('IntWidgetModel')
    default_view_name = Unicode('IntTextView')

    # Keys
    _keys = ['value', 'disabled']
    value = Int(0, help="Int value") 
    disabled = Bool(False, help="Enable or disable user changes")
