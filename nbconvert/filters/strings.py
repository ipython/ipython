"""String utilities.

Contains a collection of useful string manipulations functions.
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

# Our own imports
import textwrap #TODO

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def wrap(text, width=100):
    """ Intelligently wrap text"""

    splitt = text.split('\n')
    wrp = map(lambda x:textwrap.wrap(x,width),splitt)
    wrpd = map('\n'.join, wrp)
    return '\n'.join(wrpd)


def strip_dollars(text):
    """Remove all dollar symbols from text"""

    return text.strip('$')


#TODO: Comment me.
def rm_fake(strng):
    return strng.replace('/files/', '')


#TODO: Comment me.
def python_comment(string):
    return '# '+'\n# '.join(string.split('\n'))

def get_lines(src, start=None,end=None):
    """
    Split the input text into separate lines and then return the 
    lines that the caller is interested in.
    """
    
    # Split the input into lines.
    lines = src.split("\n")
    
    # Return the right lines.
    return "\n".join(lines[start:end]) #re-join
