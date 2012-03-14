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
from IPython.external import argparse
from IPython.nbformat import current as nbformat
from IPython.utils.text import indent


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


class ConversionException(Exception):
    pass


class Converter(object):
    default_encoding = 'utf-8'

    def __init__(self, infile):
        self.infile = infile
        self.dirpath = os.path.dirname(infile)

    @property
    def extension(self):
        raise ConversionException("""extension must be defined in Converter
                subclass""")

    def dispatch(self, cell_type):
        """return cell_type dependent render method,  for example render_code
        """
        return getattr(self, 'render_' + cell_type, unknown_cell)

    def convert(self):
        lines = []
        for cell in self.nb.worksheets[0].cells:
            conv_fn = self.dispatch(cell.cell_type)
            lines.extend(conv_fn(cell))
            lines.append('')
        return '\n'.join(lines)

    def render(self):
        "read, convert, and save self.infile"
        self.read()
        self.output = self.convert()
        return self.save()

    def read(self):
        "read and parse notebook into NotebookNode called self.nb"
        with open(self.infile) as f:
            self.nb = nbformat.read(f, 'json')

    def save(self, infile=None, encoding=None):
        "read and parse notebook into self.nb"
        if infile is None:
            infile = os.path.splitext(self.infile)[0] + '.' + self.extension
        if encoding is None:
            encoding = self.default_encoding
        with open(infile, 'w') as f:
            f.write(self.output.encode(encoding))
        return infile

    def render_heading(self, cell):
        raise NotImplementedError

    def render_code(self, cell):
        raise NotImplementedError

    def render_markdown(self, cell):
        raise NotImplementedError

    def render_pyout(self, cell):
        raise NotImplementedError

    def render_display_data(self, cell):
        raise NotImplementedError

    def render_stream(self, cell):
        raise NotImplementedError


class ConverterRST(Converter):
    extension = 'rst'
    figures_counter = 0
    heading_level = {1: '=', 2: '-', 3: '`', 4: '\'', 5: '.', 6: '~'}

    def render_heading(self, cell):
        """convert a heading cell to rst

        Returns list."""
        marker = self.heading_level[cell.level]
        return ['{0}\n{1}\n'.format(cell.source, marker * len(cell.source))]

    def render_code(self, cell):
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

    def render_markdown(self, cell):
        """convert a markdown cell to rst

        Returns list."""
        return [cell.source]

    def render_plaintext(self, cell):
        """convert plain text to rst

        Returns list."""
        return [cell.source]

    def render_pyout(self, output):
        """convert pyout part of a code cell to rst

        Returns list."""

        lines = ['Out[%s]:' % output.prompt_number, '']

        # output is a dictionary like object with type as a key
        if 'latex' in output:
            lines.extend(rst_directive('.. math::', output.latex))

        if 'text' in output:
            lines.extend(rst_directive('.. parsed-literal::', output.text))

        return lines

    def render_display_data(self, output):
        """convert display data from the output of a code cell to rst.

        Returns list.
        """
        lines = []

        if 'png' in output:
            infile = 'nb_figure_%s.png' % self.figures_counter
            fullname = os.path.join(self.dirpath, infile)
            with open(fullname, 'w') as f:
                f.write(output.png.decode('base64'))

            self.figures_counter += 1
            lines.append('.. image:: %s' % infile)
            lines.append('')

        return lines

    def render_stream(self, output):
        """convert stream part of a code cell to rst

        Returns list."""

        lines = []

        if 'text' in output:
            lines.extend(rst_directive('.. parsed-literal::', output.text))

        return lines


def rst2simplehtml(infile):
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

    cmd = "%s %s" % (cmd_template, infile)
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

    newfname = os.path.splitext(infile)[0] + '.html'
    with open(newfname, 'w') as f:
        for line in walker:
            if line.startswith('</body>'):
                break
            f.write(line)
            f.write('\n')

    return newfname


def main(infile, format='rst'):
    """Convert a notebook to html in one step"""
    if format == 'rst':
        converter = ConverterRST(infile)
        converter.render()
    elif format == 'html':
        #Currently, conversion to html is a 2 step process, nb->rst->html
        converter = ConverterRST(infile)
        rstfname = converter.render()
        rst2simplehtml(rstfname)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='nbconvert: Convert IPython notebooks to other formats')

    # TODO: consider passing file like object around, rather than filenames
    # would allow us to process stdin, or even http streams
    #parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)

    #Require a filename as a positional argument
    parser.add_argument('infile', nargs=1)
    parser.add_argument('-f', '--format', default='rst')
    args = parser.parse_args()
    main(infile=args.infile[0], format=args.format)
