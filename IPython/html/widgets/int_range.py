import os

from base import Widget
from IPython.utils.traitlets import Unicode, Int, Bool, List
from IPython.utils.javascript import display_all_js

class IntRangeWidget(Widget):
    target_name = Unicode('IntRangeWidgetModel')
    default_view_name = Unicode('IntSliderView')
    js_requirements = List(["static/notebook/js/widgets/int_range.js"])
    _keys = ['value', 'step', 'max', 'min', 'disabled', 'orientation']

    value = Int(0) 
    max = Int(100) # Max value
    min = Int(0) # Min value
    disabled = Bool(False) # Enable or disable user changes
    step = Int(1) # Minimum step that the value can take (ignored by some views)
    orientation = Unicode(u'horizontal') # Vertical or horizontal (ignored by some views)
