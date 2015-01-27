"""Int class.  

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
from .widget import DOMWidget, register
from IPython.utils.traitlets import Unicode, CInt, Bool, CaselessStrEnum, Tuple
from IPython.utils.warn import DeprecatedClass

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _Int(DOMWidget):
    """Base class used to create widgets that represent an int."""
    value = CInt(0, help="Int value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)

    def __init__(self, value=None, **kwargs):
        if value is not None:
            kwargs['value'] = value
        super(_Int, self).__init__(**kwargs)

class _BoundedInt(_Int):
    """Base class used to create widgets that represent a int that is bounded
    by a minium and maximum."""
    step = CInt(1, help="Minimum step that the value can take (ignored by some views)", sync=True)
    max = CInt(100, help="Max value", sync=True)
    min = CInt(0, help="Min value", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        super(_BoundedInt, self).__init__(*pargs, **kwargs)
        self._handle_value_changed('value', None, self.value)
        self._handle_max_changed('max', None, self.max)
        self._handle_min_changed('min', None, self.min)
        self.on_trait_change(self._handle_value_changed, 'value')
        self.on_trait_change(self._handle_max_changed, 'max')
        self.on_trait_change(self._handle_min_changed, 'min')

    def _handle_value_changed(self, name, old, new):
        """Validate value."""
        if self.min > new or new > self.max:
            self.value = min(max(new, self.min), self.max)

    def _handle_max_changed(self, name, old, new):
        """Make sure the min is always <= the max."""
        if new < self.min:
            raise ValueError("setting max < min")
        if new < self.value:
            self.value = new

    def _handle_min_changed(self, name, old, new):
        """Make sure the max is always >= the min."""
        if new > self.max:
            raise ValueError("setting min > max")
        if new > self.value:
            self.value = new

@register('IPython.IntText')
class IntText(_Int):
    """Textbox widget that represents a int."""
    _view_name = Unicode('IntTextView', sync=True)


@register('IPython.BoundedIntText')
class BoundedIntText(_BoundedInt):
    """Textbox widget that represents a int bounded by a minimum and maximum value."""
    _view_name = Unicode('IntTextView', sync=True)


@register('IPython.IntSlider')
class IntSlider(_BoundedInt):
    """Slider widget that represents a int bounded by a minimum and maximum value."""
    _view_name = Unicode('IntSliderView', sync=True)
    orientation = CaselessStrEnum(values=['horizontal', 'vertical'], 
        default_value='horizontal', allow_none=False, 
        help="Vertical or horizontal.", sync=True)
    _range = Bool(False, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)
    slider_color = Unicode(sync=True)


@register('IPython.IntProgress')
class IntProgress(_BoundedInt):
    """Progress bar that represents a int bounded by a minimum and maximum value."""
    _view_name = Unicode('ProgressView', sync=True)

    bar_style = CaselessStrEnum(
        values=['success', 'info', 'warning', 'danger', ''], 
        default_value='', allow_none=True, sync=True, help="""Use a
        predefined styling for the progess bar.""")

class _IntRange(_Int):
    value = Tuple(CInt, CInt, default_value=(0, 1), help="Tuple of (lower, upper) bounds", sync=True)
    lower = CInt(0, help="Lower bound", sync=False)
    upper = CInt(1, help="Upper bound", sync=False)
    
    def __init__(self, *pargs, **kwargs):
        value_given = 'value' in kwargs
        lower_given = 'lower' in kwargs
        upper_given = 'upper' in kwargs
        if value_given and (lower_given or upper_given):
            raise ValueError("Cannot specify both 'value' and 'lower'/'upper' for range widget")
        if lower_given != upper_given:
            raise ValueError("Must specify both 'lower' and 'upper' for range widget")
        
        super(_IntRange, self).__init__(*pargs, **kwargs)
        
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

class _BoundedIntRange(_IntRange):
    step = CInt(1, help="Minimum step that the value can take (ignored by some views)", sync=True)
    max = CInt(100, help="Max value", sync=True)
    min = CInt(0, help="Min value", sync=True)

    def __init__(self, *pargs, **kwargs):
        any_value_given = 'value' in kwargs or 'upper' in kwargs or 'lower' in kwargs
        _IntRange.__init__(self, *pargs, **kwargs)
        
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
        elif name == "max":
            if new < self.min:
                raise ValueError("setting max < min")
        
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

@register('IPython.IntRangeSlider')
class IntRangeSlider(_BoundedIntRange):
    """Slider widget that represents a pair of ints between a minimum and maximum value."""
    _view_name = Unicode('IntSliderView', sync=True)
    orientation = CaselessStrEnum(values=['horizontal', 'vertical'], 
        default_value='horizontal', allow_none=False, 
        help="Vertical or horizontal.", sync=True)
    _range = Bool(True, help="Display a range selector", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)
    slider_color = Unicode(sync=True)

# Remove in IPython 4.0
IntTextWidget = DeprecatedClass(IntText, 'IntTextWidget')
BoundedIntTextWidget = DeprecatedClass(BoundedIntText, 'BoundedIntTextWidget')
IntSliderWidget = DeprecatedClass(IntSlider, 'IntSliderWidget')
IntProgressWidget = DeprecatedClass(IntProgress, 'IntProgressWidget')
