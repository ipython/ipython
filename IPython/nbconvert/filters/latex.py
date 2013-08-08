"""Latex filters.

Module of useful filters for processing Latex within Jinja latex templates.
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

from ansi import strip_ansi

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

# Latex substitutions for escaping latex.
# see: http://stackoverflow.com/questions/16259923/how-can-i-escape-latex-special-characters-inside-django-templates
LATEX_SUBS = {
    '&':  r'\&',
    '%':  r'\%', 
    '$':  r'\$', 
    '#':  r'\#', 
    '_':  r'\_', 
    '{':  r'\{', 
    '}':  r'\}',
    '~':  r'\textasciitilde{}', 
    '^':  r'\^{}', 
    '\\': r'\textbackslash{}',
    '...': r'\ldots{}',
}


#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

__all__ = ['escape_latex',
           'strip_math_space']

def escape_latex(text):
    """
    Remove ansi codes and escape characters that may conflict with latex.

    Parameters
    ----------
    text : str
        Text containing characters that may conflict with Latex
    """

    # Remove the ansi coloring from the text and then escape it.  Escape single
    # characters first and then multiple characters.
    text = strip_ansi(text)
    text = ''.join([LATEX_SUBS.get(c, c) for c in text])
    for search, replace in LATEX_SUBS.items():
        if len(search) > 1:
            text = text.replace(search,replace)
    return text
    
    
def strip_math_space(text):
    """
    Remove the space between latex math commands and enclosing $ symbols.
    This filter is important because latex isn't as flexible as the notebook
    front end when it comes to flagging math using ampersand symbols.
    
    Parameters
    ----------
    text : str
        Text to filter.
    """

    # First, scan through the markdown looking for $.  If
    # a $ symbol is found, without a preceding \, assume
    # it is the start of a math block.  UNLESS that $ is
    # not followed by another within two math_lines.
    math_regions = []
    math_lines = 0
    within_math = False
    math_start_index = 0
    ptext = ''
    last_character = ""
    skip = False
    for index, char in enumerate(text):

        #Make sure the character isn't preceeded by a backslash
        if (char == "$" and last_character != "\\"):

            # Close the math region if this is an ending $
            if within_math:
                within_math = False
                skip = True
                ptext = ptext+'$'+text[math_start_index+1:index].strip()+'$'
                math_regions.append([math_start_index, index+1])
            else:

                # Start a new math region
                within_math = True
                math_start_index = index
                math_lines = 0

        # If we are in a math region, count the number of lines parsed.
        # Cancel the math region if we find two line breaks!
        elif char == "\n":
            if within_math:
                math_lines += 1
                if math_lines > 1:
                    within_math = False
                    ptext = ptext+text[math_start_index:index]

        # Remember the last character so we can easily watch
        # for backslashes
        last_character = char
        if not within_math and not skip:
            ptext = ptext+char
        if skip:
            skip = False
    return ptext
