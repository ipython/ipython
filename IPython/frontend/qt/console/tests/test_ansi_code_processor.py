# Standard library imports
import unittest

# Local imports
from IPython.frontend.qt.console.ansi_code_processor import AnsiCodeProcessor


class TestAnsiCodeProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = AnsiCodeProcessor()

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
                self.fail("Too many substrings.")
        self.assertEquals(i, 2, "Too few substrings.")


if __name__ == '__main__':
    unittest.main()
