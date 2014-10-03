"""Float class.  

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
from IPython.utils.traitlets import Unicode, CFloat, Bool, CaselessStrEnum, Tuple
from IPython.utils.warn import DeprecatedClass

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _Float(DOMWidget):
    value = CFloat(0.0, help="Float value", sync=True) 
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)

    def __init__(self, value=None, **kwargs):
        if value is not None:
            kwargs['value'] = value
        super(_Float, self).__init__(**kwargs)

class _BoundedFloat(_Float):
    max = CFloat(100.0, help="Max value", sync=True)
    min = CFloat(0.0, help="Min value", sync=True)
    step = CFloat(0.1, help="Minimum step that the value can take (ignored by some views)", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        super(_BoundedFloat, self).__init__(*pargs, **kwargs)
        self._validate('value', None, self.value)
        self.on_trait_change(self._validate, ['value', 'min', 'max'])

    def _validate(self, name, old, new):
        """Validate value, max, min."""
        if self.min > new or new > self.max:
            self.value = min(max(new, self.min), self.max)


class FloatText(_Float):
    _view_name = Unicode('FloatTextView', sync=True)


class BoundedFloatText(_BoundedFloat):
    _view_name = Unicode('FloatTextView', sync=True)


class FloatSlider(_BoundedFloat):
    _view_name = Unicode('FloatSliderView', sync=True)
    orientation = CaselessStrEnum(values=['horizontal', 'vertical'], 
        default_value='horizontal', 
        help="Vertical or horizontal.", allow_none=False, sync=True)
    _range = Bool(False, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)
    slider_color = Unicode(sync=True)


class FloatProgress(_BoundedFloat):
    _view_name = Unicode('ProgressView', sync=True)

    bar_style = CaselessStrEnum(
        values=['success', 'info', 'warning', 'danger', ''], 
        default_value='', allow_none=True, sync=True, help="""Use a
        predefined styling for the progess bar.""")

class _FloatRange(_Float):
    value = Tuple(CFloat, CFloat, default_value=(0.0, 1.0), help="Tuple of (lower, upper) bounds", sync=True)
    lower = CFloat(0.0, help="Lower bound", sync=False)
    upper = CFloat(1.0, help="Upper bound", sync=False)
    
    def __init__(self, *pargs, **kwargs):
        value_given = 'value' in kwargs
        lower_given = 'lower' in kwargs
        upper_given = 'upper' in kwargs
        if value_given and (lower_given or upper_given):
            raise ValueError("Cannot specify both 'value' and 'lower'/'upper' for range widget")
        if lower_given != upper_given:
            raise ValueError("Must specify both 'lower' and 'upper' for range widget")
        
        DOMWidget.__init__(self, *pargs, **kwargs)
        
        # ensure the traits match, preferring whichever (if any) was given in kwargs
        if value_given:
            self.lower, self.upper = self.value
        else:
            self.value = (self.lower, self.upper)
        
        self.on_trait_change(self._validate, ['value', 'upper', 'lower'])
    
    def _validate(self, name, old, new):
        if name == 'value':
            self.lower, self.upper = min(new), max(new)
        elif name == 'lower':
            self.value = (new, self.value[1])
        elif name == 'upper':
            self.value = (self.value[0], new)

class _BoundedFloatRange(_FloatRange):
    step = CFloat(1.0, help="Minimum step that the value can take (ignored by some views)", sync=True)
    max = CFloat(100.0, help="Max value", sync=True)
    min = CFloat(0.0, help="Min value", sync=True)
    
    def __init__(self, *pargs, **kwargs):
        any_value_given = 'value' in kwargs or 'upper' in kwargs or 'lower' in kwargs
        _FloatRange.__init__(self, *pargs, **kwargs)
        
        # ensure a minimal amount of sanity
        if self.min > self.max:
            raise ValueError("min must be <= max")
        
        if any_value_given:
            # if a value was given, clamp it within (min, max)
            self._validate("value", None, self.value)
        else:
            # otherwise, set it to 25-75% to avoid the handles overlapping
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


class FloatRangeSlider(_BoundedFloatRange):
    _view_name = Unicode('FloatSliderView', sync=True)
    orientation = CaselessStrEnum(values=['horizontal', 'vertical'], 
        default_value='horizontal', allow_none=False, 
        help="Vertical or horizontal.", sync=True)
    _range = Bool(True, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)
    slider_color = Unicode(sync=True)

# Remove in IPython 4.0
FloatTextWidget = DeprecatedClass(FloatText, 'FloatTextWidget')
BoundedFloatTextWidget = DeprecatedClass(BoundedFloatText, 'BoundedFloatTextWidget')
FloatSliderWidget = DeprecatedClass(FloatSlider, 'FloatSliderWidget')
FloatProgressWidget = DeprecatedClass(FloatProgress, 'FloatProgressWidget')
