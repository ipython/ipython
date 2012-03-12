#!/usr/bin/env python
"""A really simple notebook to rst/html exporter.

Usage

  ./nb2html.py file.ipynb

Produces 'file.rst' and 'file.html', along with auto-generated figure files
called nb_figure_NN.png.

"""

import os
import subprocess
import sys

from IPython.nbformat import current as nbformat
from IPython.utils.text import wrap_paragraphs, indent


# Cell converters

def unknown_cell(cell):
    """Default converter for cells of unknown type.
    """

    return rst_directive('.. warning:: Unknown cell') + \
      [repr(cell)]

def markdown_cell(cell):
    """convert a markdown cell to rst

    Returns list."""
    return [cell.source]


def rst_directive(directive, text=''):
    out = [directive, '']
    if text:
        out.extend([indent(text), ''])
    return out

def code_cell(cell):
    """Convert a code cell to rst

    Returns list."""

    if not cell.input:
        return []

    lines = ['In[%s]:' % cell.prompt_number, '']
    lines.extend(rst_directive('.. code:: python', cell.input))
    
    for output in cell.outputs:
        conv = converters.get(output.output_type, unknown_cell)
        lines.extend(conv(output))

    return lines

# Converters for parts of a cell.
figures_counter = 1

def out_display(output):
    """convert display data from the output of a code cell to rst.

    Returns list.
    """
    global figures_counter

    lines = []

    if 'png' in output:
        fname = 'nb_figure_%s.png' % figures_counter
        with open(fname, 'w') as f:
            f.write(output.png.decode('base64'))

        figures_counter += 1
        lines.append('.. image:: %s' % fname)
        lines.append('')
    
    return lines

    
def out_pyout(output):
    """convert pyout part of a code cell to rst

    Returns list."""

    lines = ['Out[%s]:' % output.prompt_number, '']
    
    if 'latex' in output:
        lines.extend(rst_directive('.. math::', output.latex))

    if 'text' in output:
        lines.extend(rst_directive('.. parsed-literal::', output.text))

    return lines


converters = dict(code = code_cell,
                  markdown = markdown_cell,
                  pyout = out_pyout,
                  display_data = out_display,
    )



def convert_notebook(nb):
    lines = []
    for cell in nb.worksheets[0].cells:
        conv = converters.get(cell.cell_type, unknown_cell)
        lines.extend(conv(cell))
        lines.append('')
                
    return '\n'.join(lines)


def nb2rst(fname):
    "Convert notebook to rst"
    
    with open(fname) as f:
        nb = nbformat.read(f, 'json')

    rst = convert_notebook(nb)

    newfname = os.path.splitext(fname)[0] + '.rst'
    with open(newfname, 'w') as f:
        f.write(rst.encode('utf8'))

    return newfname


def rst2simplehtml(fname):
    """Convert a rst file to simplified html suitable for blogger.

    This just runs rst2html with certain parameters to produce really simple
    html and strips the document header, so the resulting file can be easily
    pasted into a blogger edit window.
    """

    # This is the template for the rst2html call that produces the cleanest,
    # simplest html I could find.  This should help in making it easier to
    # paste into the blogspot html window, though I'm still having problems
    # with linebreaks there...
    cmd_template = ("rst2html --link-stylesheet --no-xml-declaration "
                    "--no-generator --no-datestamp --no-source-link "
                    "--no-toc-backlinks --no-section-numbering "
                    "--strip-comments ")

    cmd = "%s %s" % (cmd_template, fname)
    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
    html, stderr = proc.communicate()
    if stderr:
        raise IOError(stderr)

    # Make an iterator so breaking out holds state.  Our implementation of
    # searching for the html body below is basically a trivial little state
    # machine, so we need this.
    walker = iter(html.splitlines())

    # Find start of main text, break out to then print until we find end /div.
    # This may only work if there's a real title defined so we get a 'div class'
    # tag, I haven't really tried.
    for line in walker:
        if line.startswith('<div class'):
            break

    newfname = os.path.splitext(fname)[0] + '.html'
    with open(newfname, 'w') as f:
        for line in walker:
            if line.startswith('</div>'):
                break
            f.write(line)
            f.write('\n')
            
    return newfname


def main(fname):
    """Convert a notebook to html in one step"""
    newfname = nb2rst(fname)
    rst2simplehtml(newfname)


if __name__ == '__main__':
    main(sys.argv[1])
