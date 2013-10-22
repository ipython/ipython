from widget import Widget
from IPython.utils.traitlets import Unicode, Bool

class ContainerWidget(Widget):
    target_name = Unicode('ContainerWidgetModel')
    default_view_name = Unicode('ContainerView')
    _keys = ['_vbox', '_hbox', '_start', '_end', '_center']
    _trait_changing = False

    _hbox = Bool(False)
    _vbox = Bool(False)
    _start = Bool(False)
    _end = Bool(False)
    _center = Bool(False)
    
    def hbox(self, enabled=True):
        self._hbox = enabled
        if enabled:
            self._vbox = False
    
    def vbox(self, enabled=True):
        self._vbox = enabled
        if enabled:
            self._hbox = False
            
    def start(self, enabled=True):
        self._start = enabled
        if enabled:
            self._end = False
            self._center = False
            
    def end(self, enabled=True):
        self._end = enabled
        if enabled:
            self._start = False
            self._center = False
            
    def center(self, enabled=True):
        self._center = enabled
        if enabled:
            self._start = False
            self._end = False
