import os

from base import Widget
from IPython.utils.traitlets import Unicode
from IPython.utils.javascript import display_all_js

class ContainerWidget(Widget):
    target_name = Unicode('container_widget')
    default_view_name = Unicode('ContainerView')
    
    _keys = []
