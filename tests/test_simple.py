from nbconvert import converters, NbconvertApp
from converters.rst import ConverterRST
import nose.tools as nt

import os
import glob
import tempfile
import shutil
from IPython.nbformat import current as nbformat


class TestSimple(object):
    def setUp(self):
        """
        Create a new temporary directory and copy the input file
        'test.ipynb' there.
        """
        self.fname = 'test.ipynb'
        self.basename = os.path.splitext(self.fname)[0]
        self.wrkdir = tempfile.mkdtemp()
        self.infile = os.path.join(self.wrkdir, self.fname)
        shutil.copy(os.path.join('tests', self.fname), self.infile)

    def tearDown(self):
        shutil.rmtree(self.wrkdir)

    def outfile_exists(self, fmt):
        extension = converters[fmt].extension
        print("==out to ==>>",os.path.join(self.wrkdir,
                                           self.basename + '.' + extension))
        return os.path.exists(os.path.join(self.wrkdir,
                                           self.basename + '.' + extension))

    def test_simple(self):
        c = ConverterRST(infile=self.infile)
        f = c.render()
        nt.assert_true(f.endswith('.rst'), 'changed file extension to rst')

    def run_main(self, fmt):
        """
        Run the 'main' method to convert the input file to the given
        format and check that the expected output file exists.
        """
        app = NbconvertApp.instance()
        app.initialize()
        app.extra_args = [self.infile]
        app.fmt = fmt
        app.start()

        app.run()
        nt.assert_true(self.outfile_exists(fmt))

    def test_main(self):
        """
        Test main entry point with all known formats.
        """
        # Exclude reveal from this test because:
        # 1- AssertionError exception when there is not slideshow metadata.
        # 2- outfile_exists method can not find properly the html file.
        converters_copy = dict(converters)
        del converters_copy['reveal']
        for fmt in converters_copy:
            yield self.run_main, fmt

    def test_render_heading(self):
        """
        Unit test for cell type "heading"
        """
        # Generate and test heading cells level 1-6
        for level in xrange(1, 7):
            cell = {
                'cell_type': 'heading',
                'level': level,
                'source':  ['Test for heading type H{0}'.format(level)]
                }

            # Convert cell dictionaries to NotebookNode
            cell_nb = nbformat.NotebookNode(cell)

            # Make sure "source" attribute is uniconde not list.
            # For some reason, creating a NotebookNode manually like
            # this isn't converting source to a string like using
            # the create-from-file routine.
            if type(cell_nb.source) is list:
                cell_nb.source = '\n'.join(cell_nb.source)

            # Render to rst
            c = ConverterRST()
            rst_list = c.render_heading(cell_nb)

            # render should return a list
            nt.assert_true(isinstance(rst_list, list))
            rst_str = "".join(rst_list)

            # Confirm rst content
            chk_str = "Test for heading type H{0}\n{1}\n".format(
                 level, c.heading_level[level] * 24)
            nt.assert_equal(rst_str, chk_str)
