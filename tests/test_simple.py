from nbconvert import ConverterRST, main
import nose.tools as nt

import os
import glob
from IPython.nbformat import current as nbformat

fname = 'tests/test.ipynb'
out_fname = 'tests/test.rst'


def clean_dir():
    "Remove .rst files created during conversion"
    map(os.remove, glob.glob("./tests/*.rst"))
    map(os.remove, glob.glob("./tests/*.png"))
    map(os.remove, glob.glob("./tests/*.html"))


@nt.with_setup(clean_dir, clean_dir)
def test_simple():
    c = ConverterRST(fname)
    f = c.render()
    nt.assert_true('rst' in f, 'changed file extension to rst')


@nt.with_setup(clean_dir, clean_dir)
def test_main():
    """
    Test main entry point
    """
    main(fname)
    nt.assert_true(os.path.exists(out_fname))


def test_render_heading():
    """ Unit test for cell type "heading" """
    # Generate and test heading cells level 1-6
    for level in xrange(1, 7):
        cell = {
            'cell_type': 'heading',
            'level'    : level,
            'source'   :  ['Test for heading type H{0}'.format(level)]
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
        c = ConverterRST('')
        rst_list = c.render_heading(cell_nb)
        nt.assert_true(isinstance(rst_list, list))  # render should return a list
        rst_str = "".join(rst_list)
        # Confirm rst content
        chk_str = "Test for heading type H{0}\n{1}\n".format(
             level, c.heading_level[level] * 24)
        nt.assert_equal(rst_str, chk_str)


@nt.with_setup(clean_dir, clean_dir)
def test_main_html():
    """
    Test main entry point
    """
    main(fname, format='html')
    nt.assert_true(os.path.exists('tests/test.html'))
