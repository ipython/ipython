"""FloatRangeWidget class.  

Represents a bounded float using a widget.
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
from IPython.utils.traitlets import Unicode, Float, Bool, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class FloatRangeWidget(Widget):
    target_name = Unicode('FloatRangeWidgetModel')
    default_view_name = Unicode('FloatSliderView')

    # Keys
    _keys = ['value', 'step', 'max', 'min', 'disabled', 'orientation']
    value = Float(0.0, help="Flaot value") 
    max = Float(100.0, help="Max value")
    min = Float(0.0, help="Min value")
    disabled = Bool(False, help="Enable or disable user changes")
    step = Float(0.1, help="Minimum step that the value can take (ignored by some views)")
    orientation = Unicode(u'horizontal', help="Vertical or horizontal (ignored by some views)")
