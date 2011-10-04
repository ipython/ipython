# Standard library imports
import re
from textwrap import dedent
from unicodedata import category

# System library imports
from IPython.external.qt import QtCore, QtGui


class CallTipWidget(QtGui.QLabel):
    """ Shows call tips by parsing the current text of Q[Plain]TextEdit.
    """

    #--------------------------------------------------------------------------
    # 'QObject' interface
    #--------------------------------------------------------------------------

    def __init__(self, text_edit):
        """ Create a call tip manager that is attached to the specified Qt
            text edit widget.
        """
        assert isinstance(text_edit, (QtGui.QTextEdit, QtGui.QPlainTextEdit))
        super(CallTipWidget, self).__init__(None, QtCore.Qt.ToolTip)

        self._hide_timer = QtCore.QBasicTimer()
        self._text_edit = text_edit

        self.setFont(text_edit.document().defaultFont())
        self.setForegroundRole(QtGui.QPalette.ToolTipText)
        self.setBackgroundRole(QtGui.QPalette.ToolTipBase)
        self.setPalette(QtGui.QToolTip.palette())

        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setIndent(1)
        self.setFrameStyle(QtGui.QFrame.NoFrame)
        self.setMargin(1 + self.style().pixelMetric(
                QtGui.QStyle.PM_ToolTipLabelFrameWidth, None, self))
        self.setWindowOpacity(self.style().styleHint(
                QtGui.QStyle.SH_ToolTipLabel_Opacity, None, self, None) / 255.0)

    def eventFilter(self, obj, event):
        """ Reimplemented to hide on certain key presses and on text edit focus
            changes.
        """
        if obj == self._text_edit:
            etype = event.type()

            if etype == QtCore.QEvent.KeyPress:
                key = event.key()
                if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                    self.hide()
                elif key == QtCore.Qt.Key_Escape:
                    self.hide()
                    return True

            elif etype == QtCore.QEvent.FocusOut:
                self.hide()

            elif etype == QtCore.QEvent.Enter:
                self._hide_timer.stop()

            elif etype == QtCore.QEvent.Leave:
                self._leave_event_hide()

        return super(CallTipWidget, self).eventFilter(obj, event)

    def timerEvent(self, event):
        """ Reimplemented to hide the widget when the hide timer fires.
        """
        if event.timerId() == self._hide_timer.timerId():
            self._hide_timer.stop()
            self.hide()

    #--------------------------------------------------------------------------
    # 'QWidget' interface
    #--------------------------------------------------------------------------

    def enterEvent(self, event):
        """ Reimplemented to cancel the hide timer.
        """
        super(CallTipWidget, self).enterEvent(event)
        self._hide_timer.stop()

    def hideEvent(self, event):
        """ Reimplemented to disconnect signal handlers and event filter.
        """
        super(CallTipWidget, self).hideEvent(event)
        self._text_edit.cursorPositionChanged.disconnect(
            self._cursor_position_changed)
        self._text_edit.removeEventFilter(self)

    def leaveEvent(self, event):
        """ Reimplemented to start the hide timer.
        """
        super(CallTipWidget, self).leaveEvent(event)
        self._leave_event_hide()

    def paintEvent(self, event):
        """ Reimplemented to paint the background panel.
        """
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionFrame()
        option.initFrom(self)
        painter.drawPrimitive(QtGui.QStyle.PE_PanelTipLabel, option)
        painter.end()

        super(CallTipWidget, self).paintEvent(event)

    def setFont(self, font):
        """ Reimplemented to allow use of this method as a slot.
        """
        super(CallTipWidget, self).setFont(font)

    def showEvent(self, event):
        """ Reimplemented to connect signal handlers and event filter.
        """
        super(CallTipWidget, self).showEvent(event)
        self._text_edit.cursorPositionChanged.connect(
            self._cursor_position_changed)
        self._text_edit.installEventFilter(self)

    #--------------------------------------------------------------------------
    # 'CallTipWidget' interface
    #--------------------------------------------------------------------------

    def show_call_info(self, call_line=None, doc=None, maxlines=20):
        """ Attempts to show the specified call line and docstring at the
            current cursor location. The docstring is possibly truncated for
            length.
        """
        if doc:
            match = re.match("(?:[^\n]*\n){%i}" % maxlines, doc)
            if match:
                doc = doc[:match.end()] + '\n[Documentation continues...]'
        else:
            doc = ''

        if call_line:
            doc = '\n\n'.join([call_line, doc])
        return self.show_tip(doc)

    def show_tip(self, tip):
        """ Attempts to show the specified tip at the current cursor location.
        """
        # Attempt to find the cursor position at which to show the call tip.
        text_edit = self._text_edit
        document = text_edit.document()
        cursor = text_edit.textCursor()
        search_pos = cursor.position() - 1
        self._start_position, _ = self._find_parenthesis(search_pos,
                                                         forward=False)
        if self._start_position == -1:
            return False

        # Set the text and resize the widget accordingly.
        self.setText(tip)
        self.resize(self.sizeHint())

        # Locate and show the widget. Place the tip below the current line
        # unless it would be off the screen. In that case, place it above
        # the current line.
        padding = 3 # Distance in pixels between cursor bounds and tip box.
        cursor_rect = text_edit.cursorRect(cursor)
        screen_rect = QtGui.qApp.desktop().screenGeometry(text_edit)
        point = text_edit.mapToGlobal(cursor_rect.bottomRight())
        point.setY(point.y() + padding)
        tip_height = self.size().height()
        if point.y() + tip_height > screen_rect.height():
            point = text_edit.mapToGlobal(cursor_rect.topRight())
            point.setY(point.y() - tip_height - padding)
        self.move(point)
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
        document = self._text_edit.document()
        char = document.characterAt(position)
        # Search until a match is found or a non-printable character is
        # encountered.
        while category(char) != 'Cc' and position > 0:
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
            char = document.characterAt(position)
        else:
            position = -1
        return position, commas

    def _leave_event_hide(self):
        """ Hides the tooltip after some time has passed (assuming the cursor is
            not over the tooltip).
        """
        if (not self._hide_timer.isActive() and
            # If Enter events always came after Leave events, we wouldn't need
            # this check. But on Mac OS, it sometimes happens the other way
            # around when the tooltip is created.
            QtGui.qApp.topLevelAt(QtGui.QCursor.pos()) != self):
            self._hide_timer.start(300, self)

    #------ Signal handlers ----------------------------------------------------

    def _cursor_position_changed(self):
        """ Updates the tip based on user cursor movement.
        """
        cursor = self._text_edit.textCursor()
        if cursor.position() <= self._start_position:
            self.hide()
        else:
            position, commas = self._find_parenthesis(self._start_position + 1)
            if position != -1:
                self.hide()
