from base import Widget
from IPython.utils.traitlets import Unicode

class ContainerWidget(Widget):
    target_name = Unicode('container_widget')
    default_view_name = Unicode('ContainerView')
    