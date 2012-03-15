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
from decorators import DocInherit

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
        # XXX: unknown_cell here is RST specific - make it generic
        return getattr(self, 'render_' + cell_type, unknown_cell)

    def convert(self):
        lines = []
        lines.extend(self.optional_header())
        for cell in self.nb.worksheets[0].cells:
            conv_fn = self.dispatch(cell.cell_type)
            lines.extend(conv_fn(cell))
            lines.append('')
        lines.extend(self.optional_footer())
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

    def optional_header():
        pass

    def optional_footer():
        pass

    def render_heading(self, cell):
        """convert a heading cell

        Returns list."""
        raise NotImplementedError

    def render_code(self, cell):
        """Convert a code cell

        Returns list."""
        raise NotImplementedError

    def render_markdown(self, cell):
        """convert a markdown cell

        Returns list."""
        raise NotImplementedError

    def render_pyout(self, cell):
        """convert pyout part of a code cell

        Returns list."""
        raise NotImplementedError

    def render_display_data(self, cell):
        """convert display data from the output of a code cell

        Returns list.
        """
        raise NotImplementedError

    def render_stream(self, cell):
        """convert stream part of a code cell

        Returns list."""
        raise NotImplementedError

    def render_plaintext(self, cell):
        """convert plain text

        Returns list."""
        raise NotImplementedError


class ConverterRST(Converter):
    extension = 'rst'
    figures_counter = 0
    heading_level = {1: '=', 2: '-', 3: '`', 4: '\'', 5: '.', 6: '~'}

    @DocInherit
    def render_heading(self, cell):
        marker = self.heading_level[cell.level]
        return ['{0}\n{1}\n'.format(cell.source, marker * len(cell.source))]

    @DocInherit
    def render_code(self, cell):
        if not cell.input:
            return []

        lines = ['In[%s]:' % cell.prompt_number, '']
        lines.extend(rst_directive('.. code:: python', cell.input))

        for output in cell.outputs:
            conv_fn = self.dispatch(output.output_type)
            lines.extend(conv_fn(output))

        return lines

    @DocInherit
    def render_markdown(self, cell):
        return [cell.source]

    @DocInherit
    def render_plaintext(self, cell):
        return [cell.source]

    @DocInherit
    def render_pyout(self, output):
        lines = ['Out[%s]:' % output.prompt_number, '']

        # output is a dictionary like object with type as a key
        if 'latex' in output:
            lines.extend(rst_directive('.. math::', output.latex))

        if 'text' in output:
            lines.extend(rst_directive('.. parsed-literal::', output.text))

        return lines

    @DocInherit
    def render_display_data(self, output):
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

    @DocInherit
    def render_stream(self, output):
        lines = []

        if 'text' in output:
            lines.extend(rst_directive('.. parsed-literal::', output.text))

        return lines

class ConverterQuickHTML(Converter):
    extension = 'html'
    figures_counter = 0

    def optional_header(self):
        # XXX: inject the IPython standard CSS into here
        s = """<html>
        <head>
        </head>

        <body>
        """
        return s.splitlines()

    def optional_footer(self):
        s = """</body>
        </html>
        """
        return s.splitlines()

    @DocInherit
    def render_heading(self, cell):
        marker = cell.level
        return ['<h{1}>\n  {0}\n</h{1}>'.format(cell.source, marker)]

    @DocInherit
    def render_code(self, cell):
        if not cell.input:
            return []

        lines = ['<table>']
        lines.append('<tr><td><tt>In [<b>%s</b>]:</tt></td><td><tt>' % cell.prompt_number)
        lines.append("<br>\n".join(cell.input.splitlines()))
        lines.append('</tt></td></tr>')

        for output in cell.outputs:
            lines.append('<tr><td></td><td>')
            conv_fn = self.dispatch(output.output_type)
            lines.extend(conv_fn(output))
            lines.append('</td></tr>')
        
        lines.append('</table>')
        return lines

    @DocInherit
    def render_markdown(self, cell):
        return ["<pre>"+cell.source+"</pre>"]

    @DocInherit
    def render_plaintext(self, cell):
        return ["<pre>"+cell.source+"</pre>"]

    @DocInherit
    def render_pyout(self, output):
        lines = ['<tr><td><tt>Out[<b>%s</b>]:</tt></td></tr>' % output.prompt_number, '<td>']

        # output is a dictionary like object with type as a key
        if 'latex' in output:
            lines.append("<pre>")
            lines.extend(indent(output.latex))
            lines.append("</pre>")

        if 'text' in output:
            lines.append("<pre>")
            lines.extend(indent(output.text))
            lines.append("</pre>")

        return lines

    @DocInherit
    def render_display_data(self, output):
        lines = []

        if 'png' in output:
            infile = 'nb_figure_%s.png' % self.figures_counter
            fullname = os.path.join(self.dirpath, infile)
            with open(fullname, 'w') as f:
                f.write(output.png.decode('base64'))

            self.figures_counter += 1
            lines.append('<img src="%s">' % infile)
            lines.append('')

        return lines

    @DocInherit
    def render_stream(self, output):
        lines = []

        if 'text' in output:
            lines.append(output.text)

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
    elif format == 'quick-html':
        converter = ConverterQuickHTML(infile)
        rstfname = converter.render()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='nbconvert: Convert IPython notebooks to other formats')

    # TODO: consider passing file like object around, rather than filenames
    # would allow us to process stdin, or even http streams
    #parser.add_argument('infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)

    #Require a filename as a positional argument
    parser.add_argument('infile', nargs=1)
    parser.add_argument('-f', '--format', default='rst',
                        help='Output format. Supported formats: rst (default), html.')
    args = parser.parse_args()
    main(infile=args.infile[0], format=args.format)
