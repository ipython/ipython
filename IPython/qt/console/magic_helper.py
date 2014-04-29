"""Magic Helper - dockable widget showing magic commands for the MainWindow


Authors:

* Dimitry Kloper

"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# stdlib imports
import json
import re
import sys

# System library imports
from IPython.external.qt import QtGui,QtCore

from IPython.core.magic import magic_escapes

class MagicHelper(QtGui.QDockWidget):

    pasteRequested = QtCore.pyqtSignal(str, name = 'pasteRequested')
    runRequested = QtCore.pyqtSignal(str, name = 'runRequested')

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, name, parent):

        super(MagicHelper, self).__init__(name, parent)

        # this is a hack. The main_window reference will be used for 
        # explicit interface to kernel that must be hidden by signal/slot 
        # mechanism in the future
        self.main_window = parent

        self.data = None

        class MinListWidget(QtGui.QListWidget):
            def sizeHint(self):
                s = QtCore.QSize()
                s.setHeight(super(MinListWidget,self).sizeHint().height())
                s.setWidth(self.sizeHintForColumn(0))
                return s

        self.frame = QtGui.QFrame()
        self.search_label = QtGui.QLabel("Search:")
        self.search_line = QtGui.QLineEdit()
        self.search_class = QtGui.QComboBox()
        self.search_list = MinListWidget()
        self.paste_button = QtGui.QPushButton("Paste")
        self.run_button = QtGui.QPushButton("Run")
        
        main_layout = QtGui.QVBoxLayout()
        search_layout = QtGui.QHBoxLayout()
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_line, 10)
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.search_class)
        main_layout.addWidget(self.search_list, 10)
        action_layout = QtGui.QHBoxLayout()
        action_layout.addWidget(self.paste_button)
        action_layout.addWidget(self.run_button)
        main_layout.addLayout(action_layout)

        self.frame.setLayout(main_layout)
        self.setWidget(self.frame)

        self.visibilityChanged[bool].connect( self.update_magic_helper )
        self.search_class.activated[int].connect( 
            self.class_selected
        )
        self.search_line.textChanged[str].connect(
            self.search_changed
        )
        self.search_list.itemDoubleClicked[QtGui.QListWidgetItem].connect(
            self.paste_requested
        )
        self.paste_button.clicked[bool].connect(
            self.paste_requested
        )
        self.run_button.clicked[bool].connect(
            self.run_requested
        )

    def update_magic_helper(self, visible):
        if not visible or self.data != None:
            return
        self.data = {}
        self.search_class.clear()
        self.search_class.addItem("Populating...")
        self.main_window.active_frontend._silent_exec_callback(
            'get_ipython().magic("lsmagic")',
            self.populate_magic_helper
        )

    def populate_magic_helper(self, data):
        if not data:
            return

        if data['status'] != 'ok':
            self.main_window.log.warn(
                "%%lsmagic user-expression failed: {}".format(data)
            )
            return

        self.search_class.clear()
        self.search_list.clear()
                
        self.data = json.loads(
            data['data'].get('application/json', {})
        )
        
        self.search_class.addItem('All Magics', 'any')
        classes = set()

        for mtype in sorted(self.data):
            subdict = self.data[mtype]
            for name in sorted(subdict):
                classes.add(subdict[name])

        for cls in sorted(classes):
            label = re.sub("([a-zA-Z]+)([A-Z][a-z])","\g<1> \g<2>", cls)
            self.search_class.addItem(label, cls)

        self.filter_magic_helper('.', 'any')

    def class_selected(self, index):
        item = self.search_class.itemData(index)
        regex = self.search_line.text()
        self.filter_magic_helper(regex = regex, cls = item)

    def search_changed(self, search_string):
        item = self.search_class.itemData(
            self.search_class.currentIndex()
        )
        self.filter_magic_helper(regex = search_string, cls = item)

    def _get_current_search_item(self, item = None):
        text = None
        if not isinstance(item, QtGui.QListWidgetItem):
            item = self.search_list.currentItem()        
        text = item.text()
        return text

    def paste_requested(self, item = None):
        text = self._get_current_search_item(item)
        if text != None:
            self.pasteRequested.emit(text)

    def run_requested(self, item = None):
        text = self._get_current_search_item(item)
        if text != None:            
            self.runRequested.emit(text)

    def filter_magic_helper(self, regex, cls):
        if regex == "" or regex == None:
            regex = '.'
        if cls == None:
            cls = 'any'

        self.search_list.clear()
        for mtype in sorted(self.data):
            subdict = self.data[mtype]
            prefix = magic_escapes[mtype]

            for name in sorted(subdict):
                mclass = subdict[name]
                pmagic = prefix + name

                if (re.match(regex, name) or re.match(regex, pmagic)) and \
                   (cls == 'any' or cls == mclass): 
                    self.search_list.addItem(pmagic)

