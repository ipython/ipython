"""String filters.

Contains a collection of useful string manipulation filters for use in Jinja
templates.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import re

# Our own imports
import textwrap
from IPython.utils import coloransi
#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def wrap(text, width=100):
    """ 
    Intelligently wrap text.
    Wrap text without breaking words if possible.
    
    Parameters
    ----------
    text : str
        Text to wrap.
    width : int, optional
        Number of characters to wrap to, default 100.
    """

    split_text = text.split('\n')
    wrp = map(lambda x:textwrap.wrap(x,width), split_text)
    wrpd = map('\n'.join, wrp)
    return '\n'.join(wrpd)


def strip_dollars(text):
    """
    Remove all dollar symbols from text
    
    Parameters
    ----------
    text : str
        Text to remove dollars from
    """

    return text.strip('$')

def add_ansi_attr(ansistr, attr):
    """Adds the attribute key to the ansi colors defined
    with IPython.utils.ansicolors. Allows to boldface
    the dark characters.
    """
    return ansistr[:3]+str(attr)+ansistr[3:]

def single_ansi2latex(code):
    """Converts single ansi markup to latex format

    Return latex code and number of open brackets.
    """
    for color in coloransi.color_templates:
        colcode = getattr(coloransi.TermColors,color[0])
        # regular fonts
        if code == colcode:
            return '\\'+color[0].lower()+'{', 1
        # bold fonts
        if code == add_ansi_attr(colcode,1):
            return '\\textbf{\\textcolor{'+color[0].lower()+'}{', 2
    return '', 0

def ansi2latex(text):
    """Converts ansi formated text to latex version

    based on https://bitbucket.org/birkenfeld/sphinx-contrib/ansi.py
    """
    color_pattern = re.compile('\x1b\\[([^m]+)m')
    last_end = 0
    openbrack = 0
    outstring = ''
    for match in color_pattern.finditer(text):
        head = text[last_end:match.start()]
        formater = match.group()
        outstring += head
        if openbrack:
            outstring += '}'*openbrack
            openbrack = 0
        if match.group() <> coloransi.TermColors.Normal and not openbrack:
            texform, openbrack = single_ansi2latex(match.group())
            outstring += texform
        last_end = match.end()
    if openbrack: 
        outstring += '}'*openbrack
    outstring += text[last_end:]
    return outstring.strip()

def rm_fake(text):
    """
    Remove all occurrences of '/files/' from text
    
    Parameters
    ----------
    text : str
        Text to remove '/files/' from
    """
    return text.replace('/files/', '')


def python_comment(text):
    """
    Build a Python comment line from input text.
    
    Parameters
    ----------
    text : str
        Text to comment out.
    """
    
    #Replace line breaks with line breaks and comment symbols.
    #Also add a comment symbol at the beginning to comment out
    #the first line.
    return '# '+'\n# '.join(text.split('\n')) 


def get_lines(text, start=None,end=None):
    """
    Split the input text into separate lines and then return the 
    lines that the caller is interested in.
    
    Parameters
    ----------
    text : str
        Text to parse lines from.
    start : int, optional
        First line to grab from.
    end : int, optional
        Last line to grab from.
    """
    
    # Split the input into lines.
    lines = text.split("\n")
    
    # Return the right lines.
    return "\n".join(lines[start:end]) #re-join
