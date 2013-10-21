from base import Widget
from IPython.utils.traitlets import Unicode, Bool

class ContainerWidget(Widget):
    target_name = Unicode('container_widget')
    default_view_name = Unicode('ContainerView')
    _keys = ['vbox', 'hbox']

    hbox = Bool(True)
    vbox = Bool(False)