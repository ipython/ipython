"""Filters for processing ANSI colors within Jinja templates.
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
from IPython.utils import coloransi

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

__all__ = [
    'strip_ansi',
    'ansi2html',
    'single_ansi2latex',
    'ansi2latex'
]

def strip_ansi(source):
    """
    Remove ansi from text
    
    Parameters
    ----------
    source : str
        Source to remove the ansi from
    """
    
    return re.sub(r'\033\[(\d|;)+?m', '', source)


def ansi2html(text):
    """
    Conver ansi colors to html colors.
    
    Parameters
    ----------
    text : str
        Text containing ansi colors to convert to html
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
    text = text.replace('&', '&amp;')
    html_escapes = {
        '<': '&lt;',
        '>': '&gt;',
        "'": '&apos;',
        '"': '&quot;',
        '`': '&#96;',
    }
    
    for c, escape in html_escapes.items():
        text = text.replace(c, escape)

    ansi_re = re.compile('\x1b' + r'\[([\dA-Fa-f;]*?)m')
    m = ansi_re.search(text)
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
        text = re.sub(ansi_re, closer + opener, text, 1)

        m = ansi_re.search(text)

    if opened:
        text += '</span>'
    return text


def single_ansi2latex(code):
    """Converts single ansi markup to latex format.

    Return latex code and number of open brackets.

    Accepts codes like '\x1b[1;32m' (bold, red) and the short form '\x1b[32m' (red)

    Colors are matched to those defined in coloransi, which defines colors
    using the 0, 1 (bold) and 5 (blinking) styles. Styles 1 and 5 are
    interpreted as bold. All other styles are mapped to 0. Note that in
    coloransi, a style of 1 does not just mean bold; for example, Brown is
    "0;33", but Yellow is "1;33". An empty string is returned for unrecognised
    codes and the "reset" code '\x1b[m'.
    """
    components = code.split(';')
    if len(components) > 1:
        # Style is digits after '['
        style = int(components[0].split('[')[-1])
        color = components[1][:-1]
    else:
        style = 0
        color = components[0][-3:-1]
        
    # If the style is not normal (0), bold (1) or blinking (5) then treat it as normal
    if style not in [0, 1, 5]:
        style = 0

    for name, tcode in coloransi.color_templates:
        tstyle, tcolor = tcode.split(';')
        tstyle = int(tstyle)
        if tstyle == style and tcolor == color:
            break
    else:
        return '', 0

    if style == 5:
        name = name[5:]                             # BlinkRed -> Red, etc
    name = name.lower()

    if style in [1, 5]:
        return r'\textbf{\color{'+name+'}', 1
    else:
        return r'{\color{'+name+'}', 1

def ansi2latex(text):
    """Converts ansi formated text to latex version

    based on https://bitbucket.org/birkenfeld/sphinx-contrib/ansi.py
    """
    color_pattern = re.compile('\x1b\\[([^m]*)m')
    last_end = 0
    openbrack = 0
    outstring = ''
    for match in color_pattern.finditer(text):
        head = text[last_end:match.start()]
        outstring += head
        if openbrack:
            outstring += '}'*openbrack
            openbrack = 0
        code = match.group()
        if not (code == coloransi.TermColors.Normal or openbrack):
            texform, openbrack = single_ansi2latex(code)
            outstring += texform
        last_end = match.end()
    
    # Add the remainer of the string and THEN close any remaining color brackets.
    outstring += text[last_end:]
    if openbrack: 
        outstring += '}'*openbrack
    return outstring.strip()
