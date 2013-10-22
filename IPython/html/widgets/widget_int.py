from widget import Widget
from IPython.utils.traitlets import Unicode, Int, Bool, List

class IntWidget(Widget):
    target_name = Unicode('IntWidgetModel')
    default_view_name = Unicode('IntTextView')
    _keys = ['value', 'disabled']

    value = Int(0) 
    disabled = Bool(False) # Enable or disable user changes
