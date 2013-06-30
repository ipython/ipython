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
    'remove_ansi',
    'ansi2html',
    'single_ansi2latex',
    'ansi2latex'
]

def remove_ansi(source):
    """
    Remove ansi from text
    
    Parameters
    ----------
    source : str
        Source to remove the ansi from
    """
    
    return re.sub(r'\033\[(0|\d;\d\d)m', '', source)


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
        colcode = getattr(coloransi.TermColors,color[0])
        # regular fonts
        if code == colcode:
            return '\\'+color[0].lower()+'{', 1
        # bold fonts
        if code == colcode[:3]+str(1)+colcode[3:]:
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
