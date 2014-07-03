"""FloatWidget class.

Represents an unbounded float using a widget.
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
from IPython.utils.traitlets import Unicode, CFloat, Bool, Enum, Tuple

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _FloatWidget(DOMWidget):
    value = CFloat(0.0, help="Float value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)


class _BoundedFloatWidget(_FloatWidget):
    max = CFloat(100.0, help="Max value", sync=True)
    min = CFloat(0.0, help="Min value", sync=True)
    step = CFloat(0.1, help="Minimum step that the value can take (ignored by some views)", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self._validate('value', None, self.value)
        self.on_trait_change(self._validate, ['value', 'min', 'max'])

    def _validate(self, name, old, new):
        """Validate value, max, min."""
        if self.min > new or new > self.max:
            self.value = min(max(new, self.min), self.max)


class FloatTextWidget(_FloatWidget):
    _view_name = Unicode('FloatTextView', sync=True)


class BoundedFloatTextWidget(_BoundedFloatWidget):
    _view_name = Unicode('FloatTextView', sync=True)


class FloatSliderWidget(_BoundedFloatWidget):
    _view_name = Unicode('FloatSliderView', sync=True)
    orientation = Enum([u'horizontal', u'vertical'], u'horizontal',
        help="Vertical or horizontal.", sync=True)
    range = Bool(False, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)


class FloatProgressWidget(_BoundedFloatWidget):
    _view_name = Unicode('ProgressView', sync=True)

class _FloatRangeWidget(_FloatWidget):
    value = Tuple(CFloat, CFloat, default_value=(0.0, 1.0), help="Low and high float values", sync=True)

class _BoundedFloatRangeWidget(_FloatRangeWidget):
    step = CFloat(1.0, help="Minimum step that the value can take (ignored by some views)", sync=True)
    max = CFloat(100.0, help="Max value", sync=True)
    min = CFloat(0.0, help="Min value", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self.on_trait_change(self._validate, ['value', 'min', 'max'])

    def _validate(self, name, old, new):
        """Validate min <= low <= high <= max"""
        if name == "value":
            low, high = new
        else:
            low, high = self.value
        low = max(low, self.min)
        high = min(high, self.max)
        self.value = (min(low, high), max(low, high))


class FloatRangeSliderWidget(_BoundedFloatRangeWidget):
    _view_name = Unicode('FloatSliderView', sync=True)
    orientation = Enum([u'horizontal', u'vertical'], u'horizontal',
        help="Vertical or horizontal.", sync=True)
    range = Bool(True, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)
