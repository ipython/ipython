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
#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

__all__ = [
    'wrap',
    'strip_dollars',
    'rm_fake',
    'python_comment',
    'get_lines'
]


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
