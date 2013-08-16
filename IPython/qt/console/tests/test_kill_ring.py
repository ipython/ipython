# Standard library imports
import unittest

# System library imports
from IPython.external.qt import QtGui

# Local imports
from IPython.qt.console.kill_ring import KillRing, QtKillRing
import IPython.testing.decorators as dec

setup = dec.skip_file_no_x11(__name__)

class TestKillRing(unittest.TestCase):

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

    def test_generic(self):
        """ Does the generic kill ring work?
        """
        ring = KillRing()
        self.assertTrue(ring.yank() is None)
        self.assertTrue(ring.rotate() is None)

        ring.kill('foo')
        self.assertEqual(ring.yank(), 'foo')
        self.assertTrue(ring.rotate() is None)
        self.assertEqual(ring.yank(), 'foo')

        ring.kill('bar')
        self.assertEqual(ring.yank(), 'bar')
        self.assertEqual(ring.rotate(), 'foo')

        ring.clear()
        self.assertTrue(ring.yank() is None)
        self.assertTrue(ring.rotate() is None)

    def test_qt_basic(self):
        """ Does the Qt kill ring work?
        """
        text_edit = QtGui.QPlainTextEdit()
        ring = QtKillRing(text_edit)

        ring.kill('foo')
        ring.kill('bar')
        ring.yank()
        ring.rotate()
        ring.yank()
        self.assertEqual(text_edit.toPlainText(), 'foobar')

        text_edit.clear()
        ring.kill('baz')
        ring.yank()
        ring.rotate()
        ring.rotate()
        ring.rotate()
        self.assertEqual(text_edit.toPlainText(), 'foo')

    def test_qt_cursor(self):
        """ Does the Qt kill ring maintain state with cursor movement?
        """
        text_edit = QtGui.QPlainTextEdit()
        ring = QtKillRing(text_edit)
        
        ring.kill('foo')
        ring.kill('bar')
        ring.yank()
        text_edit.moveCursor(QtGui.QTextCursor.Left)
        ring.rotate()
        self.assertEqual(text_edit.toPlainText(), 'bar')


if __name__ == '__main__':
    import nose
    nose.main()
