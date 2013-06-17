# Standard library imports
import unittest

# System library imports
from IPython.external.qt import QtCore, QtGui

# Local imports
from IPython.qt.console.console_widget import ConsoleWidget


class TestConsoleWidget(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """ Create the application for the test case.
        """
        cls._app = QtGui.QApplication.instance()
        if cls._app is None:
            cls._app = QtGui.QApplication([])
        cls._app.setQuitOnLastWindowClosed(False)

    @classmethod
    def tearDownClass(cls):
        """ Exit the application.
        """
        QtGui.QApplication.quit()

    def test_special_characters(self):
        """ Are special characters displayed correctly?
        """
        w = ConsoleWidget()
        cursor = w._get_prompt_cursor()

        test_inputs = ['xyz\b\b=\n', 'foo\b\nbar\n', 'foo\b\nbar\r\n', 'abc\rxyz\b\b=']
        expected_outputs = [u'x=z\u2029', u'foo\u2029bar\u2029', u'foo\u2029bar\u2029', 'x=z']
        for i, text in enumerate(test_inputs):
            w._insert_plain_text(cursor, text)
            cursor.select(cursor.Document)
            selection = cursor.selectedText()
            self.assertEqual(expected_outputs[i], selection)
            # clear all the text
            cursor.insertText('')

    def test_link_handling(self):
        noKeys = QtCore.Qt
        noButton = QtCore.Qt.MouseButton(0)
        noButtons = QtCore.Qt.MouseButtons(0)
        noModifiers = QtCore.Qt.KeyboardModifiers(0)
        MouseMove = QtCore.QEvent.MouseMove
        QMouseEvent = QtGui.QMouseEvent
        
        w = ConsoleWidget()
        cursor = w._get_prompt_cursor()
        w._insert_html(cursor, '<a href="http://python.org">written in</a>')
        obj = w._control
        tip = QtGui.QToolTip
        self.assertEqual(tip.text(), u'')
        
        # should be somewhere else
        elsewhereEvent = QMouseEvent(MouseMove, QtCore.QPoint(50,50),
                                     noButton, noButtons, noModifiers)
        w.eventFilter(obj, elsewhereEvent)
        self.assertEqual(tip.isVisible(), False)
        self.assertEqual(tip.text(), u'')
        
        #self.assertEqual(tip.text(), u'')
        # should be over text
        overTextEvent = QMouseEvent(MouseMove, QtCore.QPoint(1,5),
                                    noButton, noButtons, noModifiers)
        w.eventFilter(obj, overTextEvent)
        self.assertEqual(tip.isVisible(), True)
        self.assertEqual(tip.text(), "http://python.org")
        
        # should still be over text
        stillOverTextEvent = QMouseEvent(MouseMove, QtCore.QPoint(1,5),
                                         noButton, noButtons, noModifiers)
        w.eventFilter(obj, stillOverTextEvent)
        self.assertEqual(tip.isVisible(), True)
        self.assertEqual(tip.text(), "http://python.org")
        
