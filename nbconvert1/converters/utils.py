"""A one-line description.

A longer description that spans multiple lines.  Explain the purpose of the
file and provide a short list of the key classes/functions it contains.  This
is the docstring shown when some does 'import foo;foo?' in IPython, so it
should be reasonably useful and informative.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2012, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import subprocess
import copy
import json
import re
import os
import sys

# IPython imports
from IPython.utils.text import indent
from IPython.utils import py3compat
from IPython.nbformat.v3.nbjson import BytesEncoder

# Our own imports
from lexers import IPythonLexer

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------
_multiline_outputs = ['text', 'html', 'svg', 'latex', 'javascript', 'json']


#-----------------------------------------------------------------------------
# Utility functions
#-----------------------------------------------------------------------------
def highlight(src, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source as html output.
    """
    from pygments.formatters import HtmlFormatter
    return pygment_highlight(src, HtmlFormatter(), lang)

def highlight2latex(src, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source as latex output.
    """
    from pygments.formatters import LatexFormatter
    return pygment_highlight(src, LatexFormatter(), lang)

def pygment_highlight(src, output_formatter, lang='ipython'):
    """
    Return a syntax-highlighted version of the input source
    """
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name

    if lang == 'ipython':
        lexer = IPythonLexer()
    else:
        lexer = get_lexer_by_name(lang, stripall=True)

    return highlight(src, lexer, output_formatter) 

def get_lines(src, start=None,end=None):
    """
    Split the input text into separate lines and then return the 
    lines that the caller is interested in.
    """
    
    # Split the input into lines.
    lines = src.split("\n")
    
    # Return the right lines.
    return "\n".join(lines[start:end]) #re-join

def output_container(f):
    """add a prompt-area next to an output"""
    def wrapped(self, output):
        rendered = f(self, output)
        if not rendered:
            # empty output
            return []
        lines = []
        lines.append('<div class="hbox output_area">')
        lines.extend(self._out_prompt(output))
        classes = "output_subarea output_%s" % output.output_type
        if 'html' in output.keys():
            classes += ' output_html rendered_html'
        if output.output_type == 'stream':
            classes += " output_%s" % output.stream
        lines.append('<div class="%s">' % classes)
        lines.extend(rendered)
        lines.append('</div>')  # subarea
        lines.append('</div>')  # output_area

        return lines

    return wrapped


def text_cell(f):
    """wrap text cells in appropriate divs"""
    def wrapped(self, cell):
        rendered = f(self, cell)
        classes = "text_cell_render border-box-sizing rendered_html"
        lines = ['<div class="%s">' % classes] + rendered + ['</div>']
        return lines
    return wrapped


def remove_fake_files_url(cell):
    """Remove from the cell source the /files/ pseudo-path we use.
    """
    src = cell.source
    cell.source = re.sub(r"""([\(/"'])files/""", r'\1',src)


# ANSI color functions:

def remove_ansi(src):
    """Strip all ANSI color escape sequences from input string.

    Parameters
    ----------
    src : string

    Returns
    -------
    string
    """
    return re.sub(r'\033\[(0|\d;\d\d)m', '', src)


def ansi2html(txt):
    """Render ANSI colors as HTML colors

    This is equivalent to util.fixConsole in utils.js

    Parameters
    ----------
    txt : string

    Returns
    -------
    string
    """

    ansi_colormap = {
        '30': 'ansiblack',
        '31': 'ansired',
        '32': 'ansigreen',
        '33': 'ansiyellow',
        '34': 'ansiblue',
        '35': 'ansipurple',
        '36': 'ansicyan',
        '37': 'ansigrey',
        '01': 'ansibold',
    }

    # do ampersand first
    txt = txt.replace('&', '&amp;')
    html_escapes = {
        '<': '&lt;',
        '>': '&gt;',
        "'": '&apos;',
        '"': '&quot;',
        '`': '&#96;',
    }
    for c, escape in html_escapes.iteritems():
        txt = txt.replace(c, escape)

    ansi_re = re.compile('\x1b' + r'\[([\dA-Fa-f;]*?)m')
    m = ansi_re.search(txt)
    opened = False
    cmds = []
    opener = ''
    closer = ''
    while m:
        cmds = m.groups()[0].split(';')
        closer = '</span>' if opened else ''
        # True if there is there more than one element in cmds, *or*
        # if there is only one but it is not equal to a string of zeroes.
        opened = len(cmds) > 1 or cmds[0] != '0' * len(cmds[0])
        classes = []
        for cmd in cmds:
            if cmd in ansi_colormap:
                classes.append(ansi_colormap.get(cmd))

        if classes:
            opener = '<span class="%s">' % (' '.join(classes))
        else:
            opener = ''
        txt = re.sub(ansi_re, closer + opener, txt, 1)

        m = ansi_re.search(txt)

    if opened:
        txt += '</span>'
    return txt


# Pandoc-dependent code

def markdown2latex(src):
    """Convert a markdown string to LaTeX via pandoc.

    This function will raise an error if pandoc is not installed.

    Any error messages generated by pandoc are printed to stderr.

    Parameters
    ----------
    src : string
      Input string, assumed to be valid markdown.

    Returns
    -------
    out : string
      Output as returned by pandoc.
    """
    p = subprocess.Popen('pandoc -f markdown -t latex'.split(),
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p.communicate(src.encode('utf-8'))
    if err:
        print(err, file=sys.stderr)
    #print('*'*20+'\n', out, '\n'+'*'*20)  # dbg
    return unicode(out, 'utf-8')


def markdown2rst(src):
    """Convert a markdown string to LaTeX via pandoc.

    This function will raise an error if pandoc is not installed.

    Any error messages generated by pandoc are printed to stderr.

    Parameters
    ----------
    src : string
      Input string, assumed to be valid markdown.

    Returns
    -------
    out : string
      Output as returned by pandoc.
    """
    p = subprocess.Popen('pandoc -f markdown -t rst'.split(),
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, err = p.communicate(src.encode('utf-8'))
    if err:
        print(err, file=sys.stderr)
    #print('*'*20+'\n', out, '\n'+'*'*20)  # dbg
    return unicode(out, 'utf-8')


def rst_directive(directive, text=''):
    """
    Makes ReST directive block and indents any text passed to it.
    """
    out = [directive, '']
    if text:
        out.extend([indent(text), ''])
    return out


def coalesce_streams(outputs):
    """merge consecutive sequences of stream output into single stream

    to prevent extra newlines inserted at flush calls

    TODO: handle \r deletion
    """
    new_outputs = []
    last = outputs[0]
    new_outputs = [last]
    for output in outputs[1:]:
        if (output.output_type == 'stream' and
            last.output_type == 'stream' and
            last.stream == output.stream
        ):
            last.text += output.text
        else:
            new_outputs.append(output)

    return new_outputs


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
    # This may only work if there's a real title defined so we get a 'div
    # class' tag, I haven't really tried.
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


#-----------------------------------------------------------------------------
# Cell-level functions -- similar to IPython.nbformat.v3.rwbase functions
# but at cell level instead of whole notebook level
#-----------------------------------------------------------------------------

def writes_cell(cell, **kwargs):
    kwargs['cls'] = BytesEncoder
    kwargs['indent'] = 3
    kwargs['sort_keys'] = True
    kwargs['separators'] = (',', ': ')
    if kwargs.pop('split_lines', True):
        cell = split_lines_cell(copy.deepcopy(cell))
    return py3compat.str_to_unicode(json.dumps(cell, **kwargs), 'utf-8')


def split_lines_cell(cell):
    """
    Split lines within a cell as in
    IPython.nbformat.v3.rwbase.split_lines

    """
    if cell.cell_type == 'code':
        if 'input' in cell and isinstance(cell.input, basestring):
            cell.input = (cell.input + '\n').splitlines()
        for output in cell.outputs:
            for key in _multiline_outputs:
                item = output.get(key, None)
                if isinstance(item, basestring):
                    output[key] = (item + '\n').splitlines()
    else:  # text, heading cell
        for key in ['source', 'rendered']:
            item = cell.get(key, None)
            if isinstance(item, basestring):
                cell[key] = (item + '\n').splitlines()
    return cell


def cell_to_lines(cell):
    '''
    Write a cell to json, returning the split lines.
    '''
    split_lines_cell(cell)
    s = writes_cell(cell).strip()
    return s.split('\n')
