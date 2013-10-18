from base import Widget
from IPython.utils.traitlets import Unicode, Bool, List

class BoolWidget(Widget):
    target_name = Unicode('BoolWidgetModel')
    default_view_name = Unicode('CheckboxView')
    _keys = ['value', 'description', 'disabled']
    
    value = Bool(False)
    description = Unicode('') # Description of the boolean (label).
    disabled = Bool(False) # Enable or disable user changes
    