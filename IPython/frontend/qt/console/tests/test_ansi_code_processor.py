# Standard library imports
import unittest

# Local imports
from IPython.frontend.qt.console.ansi_code_processor import AnsiCodeProcessor


class TestAnsiCodeProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = AnsiCodeProcessor()

    def test_clear(self):
        """ Do control sequences for clearing the console work?
        """
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

    def test_colors(self):
        """ Do basic controls sequences for colors work?
        """
        string = 'first\x1b[34mblue\x1b[0mlast'
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

    def test_colors_xterm(self):
        """ Do xterm-specific control sequences for colors work?
        """
        string = '\x1b]4;20;rgb:ff/ff/ff\x1b' \
            '\x1b]4;25;rgbi:1.0/1.0/1.0\x1b'
        substrings = list(self.processor.split_string(string))
        desired = { 20 : (255, 255, 255),
                    25 : (255, 255, 255) }
        self.assertEquals(self.processor.color_map, desired)

        string = '\x1b[38;5;20m\x1b[48;5;25m'
        substrings = list(self.processor.split_string(string))
        self.assertEquals(self.processor.foreground_color, 20)
        self.assertEquals(self.processor.background_color, 25)

    def test_scroll(self):
        """ Do control sequences for scrolling the buffer work?
        """
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

    def test_formfeed(self):
        """ Are formfeed characters processed correctly?
        """
        string = '\f' # form feed
        self.assertEquals(list(self.processor.split_string(string)), [''])
        self.assertEquals(len(self.processor.actions), 1)
        action = self.processor.actions[0]
        self.assertEquals(action.action, 'scroll')
        self.assertEquals(action.dir, 'down')
        self.assertEquals(action.unit, 'page')
        self.assertEquals(action.count, 1)

    def test_carriage_return(self):
        """ Are carriage return characters processed correctly?
        """
        string = 'foo\rbar' # carriage return
        splits = []
        actions = []
        for split in self.processor.split_string(string):
            splits.append(split)
            actions.append([action.action for action in self.processor.actions])
        self.assertEquals(splits, ['foo', None, 'bar'])
        self.assertEquals(actions, [[], ['carriage-return'], []])

    def test_carriage_return_newline(self):
        """transform CRLF to LF"""
        string = 'foo\rbar\r\ncat\r\n\n' # carriage return and newline
        # only one CR action should occur, and '\r\n' should transform to '\n'
        splits = []
        actions = []
        for split in self.processor.split_string(string):
            splits.append(split)
            actions.append([action.action for action in self.processor.actions])
        self.assertEquals(splits, ['foo', None, 'bar', '\r\n', 'cat', '\r\n', '\n'])
        self.assertEquals(actions, [[], ['carriage-return'], [], ['newline'], [], ['newline'], ['newline']])

    def test_beep(self):
        """ Are beep characters processed correctly?
        """
        string = 'foo\abar' # bell
        splits = []
        actions = []
        for split in self.processor.split_string(string):
            splits.append(split)
            actions.append([action.action for action in self.processor.actions])
        self.assertEquals(splits, ['foo', None, 'bar'])
        self.assertEquals(actions, [[], ['beep'], []])

    def test_backspace(self):
        """ Are backspace characters processed correctly?
        """
        string = 'foo\bbar' # backspace
        splits = []
        actions = []
        for split in self.processor.split_string(string):
            splits.append(split)
            actions.append([action.action for action in self.processor.actions])
        self.assertEquals(splits, ['foo', None, 'bar'])
        self.assertEquals(actions, [[], ['backspace'], []])

    def test_combined(self):
        """ Are CR and BS characters processed correctly in combination?

        BS is treated as a change in print position, rather than a
        backwards character deletion.  Therefore a BS at EOL is
        effectively ignored.
        """
        string = 'abc\rdef\b' # CR and backspace
        splits = []
        actions = []
        for split in self.processor.split_string(string):
            splits.append(split)
            actions.append([action.action for action in self.processor.actions])
        self.assertEquals(splits, ['abc', None, 'def', None])
        self.assertEquals(actions, [[], ['carriage-return'], [], ['backspace']])


if __name__ == '__main__':
    unittest.main()
