# Standard library imports
import unittest

# System library imports
from IPython.external.qt import QtCore, QtGui

# Local imports
from IPython.frontend.qt.console.console_widget import ConsoleWidget


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
        class event(object):
            def __init__(self, pos):
                self._pos = pos
            def pos(self):
                return self._pos
            
        w = ConsoleWidget()
        cursor = w._get_prompt_cursor()
        w._insert_html(cursor, '<a href="http://python.org">written in</a>')
        self.assertEqual(w._anchor, None)
        # should be over text
        w.mouseMoveEvent(event(QtCore.QPoint(1,5)))
        self.assertEqual(w._anchor, "http://python.org")
        # should still be over text
        w.mouseMoveEvent(event(QtCore.QPoint(5,5)))
        # should be somewhere else
        w.mouseMoveEvent(event(QtCore.QPoint(50,50)))
        self.assertEqual(w._anchor, None)
