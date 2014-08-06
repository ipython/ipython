import os
from unittest import TestCase

from IPython.utils.py3compat import unicode_type
from .. import parse_filename


class MiscTests(TestCase):

    def check_filename(self, path, exp_fname, exp_bname, exp_format):
        fname, bname, format = parse_filename(path)
        self.assertEqual(fname, exp_fname)
        self.assertEqual(bname, exp_bname)
        self.assertEqual(format, exp_format)

    def test_parse_filename(self):

        # check format detection
        self.check_filename("test.ipynb", "test.ipynb", "test", "json")
        self.check_filename("test.json", "test.json", "test", "json")
        self.check_filename("test.py", "test.py", "test", "py")

        # check parsing an unknown format
        self.check_filename("test.nb", "test.nb.ipynb", "test.nb", "json")

        # check parsing a full file path
        abs_path = os.path.abspath("test.ipynb")
        basename, ext = os.path.splitext(abs_path)
        self.check_filename(abs_path, abs_path, basename, "json")

        # check parsing a file name containing dots
        self.check_filename("test.nb.ipynb", "test.nb.ipynb", "test.nb",
                            "json")
