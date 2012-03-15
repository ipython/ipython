from . import PageObject

class Dashboard(PageObject):
    def __init__(self):
        PageObject.__init__(self, '/')
