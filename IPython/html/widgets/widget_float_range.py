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
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Float, Bool, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class BoundedFloatTextWidget(DOMWidget):
    view_name = Unicode('FloatTextView', sync=True)
    value = Float(0.0, help="Float value", sync=True) 
    max = Float(100.0, help="Max value", sync=True)
    min = Float(0.0, help="Min value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    step = Float(0.1, help="Minimum step that the value can take (ignored by some views)", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)


class FloatSliderWidget(BoundedFloatTextWidget):
    view_name = Unicode('FloatSliderView', sync=True)
    orientation = Unicode(u'horizontal', help="Vertical or horizontal.", sync=True)


class FloatProgressWidget(BoundedFloatTextWidget):
    view_name = Unicode('ProgressView', sync=True)
