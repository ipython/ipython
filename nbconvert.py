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


def rst_directive(directive, text=''):
    out = [directive, '']
    if text:
        out.extend([indent(text), ''])
    return out

# Converters for parts of a cell.
figures_counter = 1

class ConversionException(Exception):
    pass

class Converter(object):
    default_encoding = 'utf-8'
    def __init__(self, fname):
        self.fname = fname

    @property
    def extension(self):
        raise ConversionException("""extension must be defined in Converter
                subclass""")

    def dispatch(self,cell_type):
        """return cell_type dependent render method,  for example render_code
        """
        return getattr(self, 'render_'+cell_type, unknown_cell)

    def convert(self):
        lines = []
        for cell in self.nb.worksheets[0].cells:
            conv_fn = self.dispatch(cell.cell_type)
            lines.extend(conv_fn(cell))
            lines.append('')
        return '\n'.join(lines)

    def render(self):
        "read, convert, and save self.fname"
        self.read()
        self.output = self.convert()
        return self.save()

    def read(self):
        "read and parse notebook into NotebookNode called self.nb"
        with open(self.fname) as f:
            self.nb = nbformat.read(f, 'json')

    def save(self,fname=None, encoding=None):
        "read and parse notebook into self.nb"
        if fname is None:
            fname = os.path.splitext(self.fname)[0] + '.' + self.extension
        if encoding is None:
            encoding = self.default_encoding
        with open(fname, 'w') as f:
            f.write(self.output.encode(encoding))
        return fname

    def render_heading(self,cell):
         raise NotImplementedError
    def render_code(self,cell):
         raise NotImplementedError
    def render_markdown(self,cell):
         raise NotImplementedError
    def render_pyout(self,cell):
         raise NotImplementedError
    def render_display_data(self,cell):
         raise NotImplementedError

class ConverterRST(Converter):
    extension = 'rst'
    def render_heading(self,cell):
        """convert a heading cell to rst

        Returns list."""
        heading_level = {1:'=', 2:'-', 3:'`', 4:'\'', 5:'.',6:'~'}
        marker = heading_level[cell.level]
        return ['{0}\n{1}\n'.format(cell.source, marker*len(cell.source))]

    def render_code(self,cell):
        """Convert a code cell to rst

        Returns list."""

        if not cell.input:
            return []

        lines = ['In[%s]:' % cell.prompt_number, '']
        lines.extend(rst_directive('.. code:: python', cell.input))

        for output in cell.outputs:
            conv_fn = self.dispatch(output.output_type)
            lines.extend(conv_fn(output))

        return lines

    def render_markdown(self,cell):
        """convert a markdown cell to rst

        Returns list."""
        return [cell.source]

    def render_pyout(self,output):
        """convert pyout part of a code cell to rst

        Returns list."""

        lines = ['Out[%s]:' % output.prompt_number, '']
        
        if 'latex' in output:
            lines.extend(rst_directive('.. math::', output.latex))

        if 'text' in output:
            lines.extend(rst_directive('.. parsed-literal::', output.text))

        return lines

    def render_display_data(self,output):
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
        if line.startswith('<body>'):
            break

    newfname = os.path.splitext(fname)[0] + '.html'
    with open(newfname, 'w') as f:
        for line in walker:
            if line.startswith('</body>'):
                break
            f.write(line)
            f.write('\n')
            
    return newfname


def main(fname):
    """Convert a notebook to html in one step"""
    newfname = nb2rst(fname)
    #rst2simplehtml(newfname)


if __name__ == '__main__':
    main(sys.argv[1])
