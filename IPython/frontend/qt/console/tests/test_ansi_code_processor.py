# Standard library imports
import unittest

# Local imports
from IPython.frontend.qt.console.ansi_code_processor import AnsiCodeProcessor


class TestAnsiCodeProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = AnsiCodeProcessor()

    def testClear(self):
        string = '\x1b[2J\x1b[K'
        i = -1
        for i, substring in enumerate(self.processor.split_string(string)):
            if i == 0:
                self.assertEquals(len(self.processor.actions), 1)
                action = self.processor.actions[0]
                self.assertEquals(action.action, 'erase')
                self.assertEquals(action.area, 'screen')
                self.assertEquals(action.erase_to, 'all')
            elif i == 1:
                self.assertEquals(len(self.processor.actions), 1)
                action = self.processor.actions[0]
                self.assertEquals(action.action, 'erase')
                self.assertEquals(action.area, 'line')
                self.assertEquals(action.erase_to, 'end')
            else:
                self.fail('Too many substrings.')
        self.assertEquals(i, 1, 'Too few substrings.')

    def testColors(self):
        string = "first\x1b[34mblue\x1b[0mlast"
        i = -1
        for i, substring in enumerate(self.processor.split_string(string)):
            if i == 0:
                self.assertEquals(substring, 'first')
                self.assertEquals(self.processor.foreground_color, None)
            elif i == 1:
                self.assertEquals(substring, 'blue')
                self.assertEquals(self.processor.foreground_color, 4)
            elif i == 2:
                self.assertEquals(substring, 'last')
                self.assertEquals(self.processor.foreground_color, None)
            else:
                self.fail('Too many substrings.')
        self.assertEquals(i, 2, 'Too few substrings.')

    def testScroll(self):
        string = '\x1b[5S\x1b[T'
        i = -1
        for i, substring in enumerate(self.processor.split_string(string)):
            if i == 0:
                self.assertEquals(len(self.processor.actions), 1)
                action = self.processor.actions[0]
                self.assertEquals(action.action, 'scroll')
                self.assertEquals(action.dir, 'up')
                self.assertEquals(action.unit, 'line')
                self.assertEquals(action.count, 5)
            elif i == 1:
                self.assertEquals(len(self.processor.actions), 1)
                action = self.processor.actions[0]
                self.assertEquals(action.action, 'scroll')
                self.assertEquals(action.dir, 'down')
                self.assertEquals(action.unit, 'line')
                self.assertEquals(action.count, 1)
            else:
                self.fail('Too many substrings.')
        self.assertEquals(i, 1, 'Too few substrings.')

    def testSpecials(self):
        string = '\f' # form feed
        self.assertEquals(list(self.processor.split_string(string)), [''])
        self.assertEquals(len(self.processor.actions), 1)
        action = self.processor.actions[0]
        self.assertEquals(action.action, 'scroll')
        self.assertEquals(action.dir, 'down')
        self.assertEquals(action.unit, 'page')
        self.assertEquals(action.count, 1)


if __name__ == '__main__':
    unittest.main()
