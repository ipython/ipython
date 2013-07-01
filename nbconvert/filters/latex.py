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
import re

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

#Latex substitutions for escaping latex.
LATEX_SUBS = (
    (re.compile('\033\[[0-9;]+m'),''),  # handle console escapes
    (re.compile(r'\\'), r'\\textbackslash'),
    (re.compile(r'([{}_#%&$])'), r'\\\1'),
    (re.compile(r'~'), r'\~{}'),
    (re.compile(r'\^'), r'\^{}'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\.\.\.+'), r'\\ldots'),
)

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def escape_latex(text):
    """
    Escape characters that may conflict with latex.
    
    Parameters
    ----------
    text : str
        Text containing characters that may conflict with Latex
    """
    return_text = text
    for pattern, replacement in LATEX_SUBS:
        return_text = pattern.sub(replacement, return_text)
    return return_text
    
    
def rm_math_space(text):
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
