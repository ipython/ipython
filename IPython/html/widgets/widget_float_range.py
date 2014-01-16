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
from IPython.utils.traitlets import Unicode, CFloat, Bool, List, Enum

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class BoundedFloatTextWidget(DOMWidget):
    view_name = Unicode('FloatTextView', sync=True)
    value = CFloat(0.0, help="Float value", sync=True) 
    max = CFloat(100.0, help="Max value", sync=True)
    min = CFloat(0.0, help="Min value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    step = CFloat(0.1, help="Minimum step that the value can take (ignored by some views)", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self.on_trait_change(self._validate, ['value', 'min', 'max'])

    def _validate(self, name, old, new):
        """Validate value, max, min"""
        if self.min > new or new > self.max:
            self.value = min(max(new, self.min), self.max)


class FloatSliderWidget(BoundedFloatTextWidget):
    view_name = Unicode('FloatSliderView', sync=True)
    orientation = Enum([u'horizontal', u'vertical'], u'horizontal', 
        help="Vertical or horizontal.", sync=True)


class FloatProgressWidget(BoundedFloatTextWidget):
    view_name = Unicode('ProgressView', sync=True)
