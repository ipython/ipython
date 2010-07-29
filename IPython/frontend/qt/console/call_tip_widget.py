# Standard library imports
import re
from textwrap import dedent

# System library imports
from PyQt4 import QtCore, QtGui


class CallTipWidget(QtGui.QLabel):
    """ Shows call tips by parsing the current text of Q[Plain]TextEdit.
    """

    #--------------------------------------------------------------------------
    # 'QWidget' interface
    #--------------------------------------------------------------------------

    def __init__(self, parent):
        """ Create a call tip manager that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(parent, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        QtGui.QLabel.__init__(self, parent, QtCore.Qt.ToolTip)

        self.setFont(parent.document().defaultFont())
        self.setForegroundRole(QtGui.QPalette.ToolTipText)
        self.setBackgroundRole(QtGui.QPalette.ToolTipBase)
        self.setPalette(QtGui.QToolTip.palette())

        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setIndent(1)
        self.setFrameStyle(QtGui.QFrame.NoFrame)
        self.setMargin(1 + self.style().pixelMetric(
                QtGui.QStyle.PM_ToolTipLabelFrameWidth, None, self))
        self.setWindowOpacity(self.style().styleHint(
                QtGui.QStyle.SH_ToolTipLabel_Opacity, None, self) / 255.0)

    def hideEvent(self, event):
        """ Reimplemented to disconnect the cursor movement handler.
        """
        QtGui.QListWidget.hideEvent(self, event)
        self.parent().cursorPositionChanged.disconnect(self._update_tip)

    def paintEvent(self, event):
        """ Reimplemented to paint the background panel.
        """
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionFrame()
        option.init(self)
        painter.drawPrimitive(QtGui.QStyle.PE_PanelTipLabel, option)
        painter.end()

        QtGui.QLabel.paintEvent(self, event)

    def showEvent(self, event):
        """ Reimplemented to connect the cursor movement handler.
        """
        QtGui.QListWidget.showEvent(self, event)
        self.parent().cursorPositionChanged.connect(self._update_tip)

    #--------------------------------------------------------------------------
    # 'CallTipWidget' interface
    #--------------------------------------------------------------------------

    def show_docstring(self, doc, maxlines=20):
        """ Attempts to show the specified docstring at the current cursor
            location. The docstring is dedented and possibly truncated for
            length.
        """
        doc = dedent(doc.rstrip()).lstrip()
        match = re.match("(?:[^\n]*\n){%i}" % maxlines, doc)
        if match:
            doc = doc[:match.end()] + '\n[Documentation continues...]'
        return self.show_tip(doc)

    def show_tip(self, tip):
        """ Attempts to show the specified tip at the current cursor location.
        """
        text_edit = self.parent()
        document = text_edit.document()
        cursor = text_edit.textCursor()
        search_pos = cursor.position() - 1
        self._start_position, _ = self._find_parenthesis(search_pos, 
                                                         forward=False)
        if self._start_position == -1:
            return False
    
        point = text_edit.cursorRect(cursor).bottomRight()
        point = text_edit.mapToGlobal(point)
        self.move(point)
        self.setText(tip)
        if self.isVisible():
            self.resize(self.sizeHint())
        else:
            self.show()
        return True
            
    #--------------------------------------------------------------------------
    # Protected interface
    #--------------------------------------------------------------------------

    def _find_parenthesis(self, position, forward=True):
        """ If 'forward' is True (resp. False), proceed forwards
            (resp. backwards) through the line that contains 'position' until an
            unmatched closing (resp. opening) parenthesis is found. Returns a
            tuple containing the position of this parenthesis (or -1 if it is
            not found) and the number commas (at depth 0) found along the way.
        """
        commas = depth = 0
        document = self.parent().document()
        qchar = document.characterAt(position)
        while (position > 0 and qchar.isPrint() and 
               # Need to check explicitly for line/paragraph separators:
               qchar.unicode() not in (0x2028, 0x2029)):
            char = qchar.toAscii()
            if char == ',' and depth == 0:
                commas += 1
            elif char == ')':
                if forward and depth == 0:
                    break
                depth += 1
            elif char == '(':
                if not forward and depth == 0:
                    break
                depth -= 1
            position += 1 if forward else -1
            qchar = document.characterAt(position)
        else:
            position = -1
        return position, commas

    def _highlight_tip(self, tip, current_argument):
        """ Highlight the current argument (arguments start at 0), ending at the
            next comma or unmatched closing parenthesis.
            
            FIXME: This is an unreliable way to do things and it isn't being
                   used right now. Instead, we should use inspect.getargspec
                   metadata for this purpose.
        """
        start = tip.find('(')
        if start != -1:
            for i in xrange(current_argument):
                start = tip.find(',', start)
            if start != -1:
                end = start + 1
                while end < len(tip):
                    char = tip[end]
                    depth = 0
                    if (char == ',' and depth == 0):
                        break
                    elif char == '(':
                        depth += 1
                    elif char == ')':
                        if depth == 0:
                            break
                        depth -= 1
                    end += 1
                tip = tip[:start+1] + '<font color="blue">' + \
                    tip[start+1:end] + '</font>' + tip[end:]
                tip = tip.replace('\n', '<br/>')
        return tip

    def _update_tip(self):
        """ Updates the tip based on user cursor movement.
        """
        cursor = self.parent().textCursor()
        if cursor.position() <= self._start_position:
            self.hide()
        else:
            position, commas = self._find_parenthesis(self._start_position + 1)
            if position != -1:
                self.hide()
