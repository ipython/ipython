import os

from base import Widget
from IPython.utils.traitlets import Unicode, List, Bool
from IPython.utils.javascript import display_all_js

class SelectionWidget(Widget):
    target_name = Unicode('SelectionWidgetModel')
    default_view_name = Unicode('DropdownView')
    js_requirements = List(["static/notebook/js/widgets/selection.js"])
    _keys = ['value', 'values', 'disabled']

    value = Unicode()
    values = List() # List of values the user can select
    disabled = Bool(False) # Enable or disable user changes
 