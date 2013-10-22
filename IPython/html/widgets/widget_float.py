from widget import Widget
from IPython.utils.traitlets import Unicode, Float, Bool, List

class FloatWidget(Widget):
    target_name = Unicode('FloatWidgetModel')
    default_view_name = Unicode('FloatTextView')
    _keys = ['value', 'disabled']
    
    value = Float(0.0) 
    disabled = Bool(False) # Enable or disable user changes
