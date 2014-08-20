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
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, CInt, Bool, Enum, Tuple

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _IntWidget(DOMWidget):
    value = CInt(0, help="Int value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)


class _BoundedIntWidget(_IntWidget):
    step = CInt(1, help="Minimum step that the value can take (ignored by some views)", sync=True)
    max = CInt(100, help="Max value", sync=True)
    min = CInt(0, help="Min value", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self.on_trait_change(self._validate, ['value', 'min', 'max'])

    def _validate(self, name, old, new):
        """Validate value, max, min."""
        if self.min > new or new > self.max:
            self.value = min(max(new, self.min), self.max)


class IntTextWidget(_IntWidget):
    _view_name = Unicode('IntTextView', sync=True)


class BoundedIntTextWidget(_BoundedIntWidget):
    _view_name = Unicode('IntTextView', sync=True)


class IntSliderWidget(_BoundedIntWidget):
    _view_name = Unicode('IntSliderView', sync=True)
    orientation = Enum([u'horizontal', u'vertical'], u'horizontal',
        help="Vertical or horizontal.", sync=True)
    range = Bool(False, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)


class IntProgressWidget(_BoundedIntWidget):
    _view_name = Unicode('ProgressView', sync=True)

class _IntRangeWidget(_IntWidget):
    value = Tuple(CInt, CInt, default_value=(0, 1), help="Tuple of (lower, upper) bounds", sync=True)
    lower = CInt(0, help="Lower bound", sync=False)
    upper = CInt(1, help="Upper bound", sync=False)
    
    def __init__(self, *pargs, **kwargs):
        if 'value' in kwargs and ('lower' in kwargs or 'upper' in kwargs):
            raise ValueError("Cannot specify both 'value' and 'lower'/'upper' for range widget")
        
        value_given = 'value' in kwargs
        
        DOMWidget.__init__(self, *pargs, **kwargs)
        
        # ensure the traits match, preferring whichever (if any) was given in kwargs
        if value_given:
            self.lower, self.upper = self.value
        else:
            self.value = (self.lower, self.upper)

        self.on_trait_change(self._validate, ['value', 'upper', 'lower'])
    
    def _validate(self, name, old, new):
        print '_IntRangeWidget::_validate', name, old, new
        if name == 'value':
            self.lower, self.upper = min(new), max(new)
        elif name == 'lower':
            self.value = (new, self.value[1])
        elif name == 'upper':
            self.value = (self.value[0], new)

class _BoundedIntRangeWidget(_IntRangeWidget):
    step = CInt(1, help="Minimum step that the value can take (ignored by some views)", sync=True)
    max = CInt(100, help="Max value", sync=True)
    min = CInt(0, help="Min value", sync=True)

    def __init__(self, *pargs, **kwargs):
        any_value_given = 'value' in kwargs or 'upper' in kwargs or 'lower' in kwargs
        _IntRangeWidget.__init__(self, *pargs, **kwargs)
        
        # ensure a minimal amount of sanity
        if self.min > self.max:
            raise ValueError("min must be <= max")
        
        # ensure the initial values within bounds
        if self.lower < self.min:
            self.lower = self.min
            
        if self.upper > self.max:
            self.upper = self.max
        
        # if no value (or upper/lower) is set, use 25-75% to avoid the handles overlapping
        if not any_value_given:
            self.value = (0.75*self.min + 0.25*self.max,
                          0.25*self.min + 0.75*self.max)
        # callback already set for 'value', 'lower', 'upper'
        self.on_trait_change(self._validate, ['min', 'max'])

    def _validate(self, name, old, new):
        if name == "min":
            if new > self.max:
                raise ValueError("setting min > max")
            self.min = new
        elif name == "max":
            if new < self.min:
                raise ValueError("setting max < min")
            self.max = new
        
        low, high = self.value
        if name == "value":
            low, high = min(new), max(new)
        elif name == "upper":
            if new < self.lower:
                raise ValueError("setting upper < lower")
            high = new
        elif name == "lower":
            if new > self.upper:
                raise ValueError("setting lower > upper")
            low = new
        
        low = max(self.min, min(low, self.max))
        high = min(self.max, max(high, self.min))
        
        # determine the order in which we should update the
        # lower, upper traits to avoid a temporary inverted overlap
        lower_first = high < self.lower
        
        self.value = (low, high)
        if lower_first:
            self.lower = low
            self.upper = high
        else:
            self.upper = high
            self.lower = low

class IntRangeSliderWidget(_BoundedIntRangeWidget):
    _view_name = Unicode('IntSliderView', sync=True)
    orientation = Enum([u'horizontal', u'vertical'], u'horizontal',
        help="Vertical or horizontal.", sync=True)
    range = Bool(True, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)
