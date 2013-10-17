import os

from base import Widget
from IPython.utils.traitlets import Unicode, Bool, List
from IPython.utils.javascript import display_all_js

class StringWidget(Widget):
    target_name = Unicode('StringWidgetModel')
    default_view_name = Unicode('TextboxView')
    js_requirements = List(["notebook/js/widgets/string.js"])
    _keys = ['value', 'row_count', 'disabled']
    
    value = Unicode()
    disabled = Bool(False) # Enable or disable user changes
    