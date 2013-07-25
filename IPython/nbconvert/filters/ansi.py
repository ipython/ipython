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
    
    for c, escape in html_escapes.iteritems():
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
    """Converts single ansi markup to latex format

    Return latex code and number of open brackets.
    """
    for color in coloransi.color_templates:

        #Make sure to get the color code (which is a part of the overall style)
        # i.e.  0;31 is valid
        #       31 is also valid, and means the same thing
        #coloransi.color_templates stores the longer of the two formats %d;%d
        #Get the short format so we can parse that too.  Short format only exist
        #if no other formating is applied (the other number must be a 0)!
        style_code = getattr(coloransi.TermColors, color[0])
        color_code = style_code.split(';')[1]
        is_normal = style_code.split(';')[0] == '0'

        # regular fonts
        if (code == style_code) or (is_normal and code == color_code):
            return '\\'+color[0].lower()+'{', 1
        # bold fonts
        if code == style_code[:3]+str(1)+style_code[3:]:
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
        outstring += head
        if openbrack:
            outstring += '}'*openbrack
            openbrack = 0
        if not (match.group() == coloransi.TermColors.Normal or openbrack):
            texform, openbrack = single_ansi2latex(match.group())
            outstring += texform
        last_end = match.end()

    #Add the remainer of the string and THEN close any remaining color brackets.
    outstring += text[last_end:]
    if openbrack: 
        outstring += '}'*openbrack
    return outstring.strip()
