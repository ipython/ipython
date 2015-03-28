"""MagicHelper - dockable widget showing magic commands for the MainWindow
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License. 

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
    """MagicHelper - dockable widget for convenient search and running of
                     magic command for IPython QtConsole.
    """

    #---------------------------------------------------------------------------
    # signals
    #---------------------------------------------------------------------------

    pasteRequested = QtCore.Signal(str, name = 'pasteRequested')
    """This signal is emitted when user wants to paste selected magic 
       command into the command line.
    """

    runRequested = QtCore.Signal(str, name = 'runRequested')
    """This signal is emitted when user wants to execute selected magic command
    """

    readyForUpdate = QtCore.Signal(name = 'readyForUpdate')
    """This signal is emitted when MagicHelper is ready to be populated.
       Since kernel querying mechanisms are out of scope of this class,
       it expects its owner to invoke MagicHelper.populate_magic_helper()
       as a reaction on this event.
    """

    #---------------------------------------------------------------------------
    # constructor
    #---------------------------------------------------------------------------

    def __init__(self, name, parent):
        super(MagicHelper, self).__init__(name, parent)

        self.data = None

        class MinListWidget(QtGui.QListWidget):
            """Temp class to overide the default QListWidget size hint
               in order to make MagicHelper narrow
            """
            def sizeHint(self):
                s = QtCore.QSize()
                s.setHeight(super(MinListWidget,self).sizeHint().height())
                s.setWidth(self.sizeHintForColumn(0))
                return s

        # construct content
        self.frame = QtGui.QFrame()
        self.search_label = QtGui.QLabel("Search:")
        self.search_line = QtGui.QLineEdit()
        self.search_class = QtGui.QComboBox()
        self.search_list = MinListWidget()
        self.paste_button = QtGui.QPushButton("Paste")
        self.run_button = QtGui.QPushButton("Run")
        
        # layout all the widgets
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

        # connect all the relevant signals to handlers
        self.visibilityChanged[bool].connect( self._update_magic_helper )
        self.search_class.activated[int].connect( 
            self.class_selected
        )
        self.search_line.textChanged[str].connect(
            self.search_changed
        )
        self.search_list.itemDoubleClicked.connect(
            self.paste_requested
        )
        self.paste_button.clicked[bool].connect(
            self.paste_requested
        )
        self.run_button.clicked[bool].connect(
            self.run_requested
        )

    #---------------------------------------------------------------------------
    # implementation
    #---------------------------------------------------------------------------

    def _update_magic_helper(self, visible):
        """Start update sequence. 
           This method is called when MagicHelper becomes visible. It clears
           the content and emits readyForUpdate signal. The owner of the 
           instance is expected to invoke populate_magic_helper() when magic
           info is available.
        """
        if not visible or self.data is not None:
            return
        self.data = {}
        self.search_class.clear()
        self.search_class.addItem("Populating...")
        self.search_list.clear()
        self.readyForUpdate.emit()

    def populate_magic_helper(self, data):
        """Expects data returned by lsmagics query from kernel.
           Populates the search_class and search_list with relevant items.
        """
        self.search_class.clear()
        self.search_list.clear()
                
        self.data = data['data'].get('application/json', {})
        
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
        """Handle search_class selection changes
        """
        item = self.search_class.itemData(index)
        regex = self.search_line.text()
        self.filter_magic_helper(regex = regex, cls = item)

    def search_changed(self, search_string):
        """Handle search_line text changes.
           The text is interpreted as a regular expression
        """
        item = self.search_class.itemData(
            self.search_class.currentIndex()
        )
        self.filter_magic_helper(regex = search_string, cls = item)

    def _get_current_search_item(self, item = None):
        """Retrieve magic command currently selected in the search_list
        """
        text = None
        if not isinstance(item, QtGui.QListWidgetItem):
            item = self.search_list.currentItem()        
        text = item.text()
        return text

    def paste_requested(self, item = None):
        """Emit pasteRequested signal with currently selected item text
        """
        text = self._get_current_search_item(item)
        if text is not None:
            self.pasteRequested.emit(text)

    def run_requested(self, item = None):
        """Emit runRequested signal with currently selected item text
        """
        text = self._get_current_search_item(item)
        if text is not None:
            self.runRequested.emit(text)

    def filter_magic_helper(self, regex, cls):
        """Update search_list with magic commands whose text match
           regex and class match cls.
           If cls equals 'any' - any class matches.
        """
        if regex == "" or regex is None:
            regex = '.'
        if cls is None:
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

