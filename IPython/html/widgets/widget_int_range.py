"""IntRangeWidget class.  

Represents a bounded int using a widget.
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
from IPython.utils.traitlets import Unicode, CInt, Bool, List

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class BoundedIntTextWidget(DOMWidget):
    view_name = Unicode('IntTextView', sync=True)

    # Keys
    value = CInt(0, help="Int value", sync=True) 
    max = CInt(100, help="Max value", sync=True)
    min = CInt(0, help="Min value", sync=True)
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    step = CInt(1, help="Minimum step that the value can take (ignored by some views)", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self.on_trait_change(self._validate, ['value', 'min', 'max'])

    def _validate(self, name, old, new):
        """Validate value, max, min"""
        if self.min > new or new > self.max:
            self.value = min(max(new, self.min), self.max)


class IntSliderWidget(BoundedIntTextWidget):
    view_name = Unicode('IntSliderView', sync=True)
    orientation = Unicode(u'horizontal', help="Vertical or horizontal.", sync=True)


class IntProgressWidget(BoundedIntTextWidget):
    view_name = Unicode('ProgressView', sync=True)
