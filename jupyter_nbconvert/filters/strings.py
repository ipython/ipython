# coding: utf-8
"""String filters.

Contains a collection of useful string manipulation filters for use in Jinja
templates.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import re
import textwrap
try:
    from urllib.parse import quote  # Py 3
except ImportError:
    from urllib2 import quote  # Py 2
from xml.etree import ElementTree

from IPython.core.interactiveshell import InteractiveShell
from IPython.utils import py3compat


__all__ = [
    'wrap_text',
    'html2text',
    'add_anchor',
    'strip_dollars',
    'strip_files_prefix',
    'comment_lines',
    'get_lines',
    'ipython2python',
    'posix_path',
    'path2url',
    'add_prompts',
    'ascii_only',
    'prevent_list_blocks',
]


def wrap_text(text, width=100):
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


def html2text(element):
    """extract inner text from html
    
    Analog of jQuery's $(element).text()
    """
    if isinstance(element, py3compat.string_types):
        try:
            element = ElementTree.fromstring(element)
        except Exception:
            # failed to parse, just return it unmodified
            return element
    
    text = element.text or ""
    for child in element:
        text += html2text(child)
    text += (element.tail or "")
    return text


def add_anchor(html):
    """Add an anchor-link to an html header
    
    For use on markdown headings
    """
    try:
        h = ElementTree.fromstring(py3compat.cast_bytes_py2(html, encoding='utf-8'))
    except Exception:
        # failed to parse, just return it unmodified
        return html
    link = html2text(h).replace(' ', '-')
    h.set('id', link)
    a = ElementTree.Element("a", {"class" : "anchor-link", "href" : "#" + link})
    a.text = u'¶'
    h.append(a)

    # Known issue of Python3.x, ElementTree.tostring() returns a byte string
    # instead of a text string.  See issue http://bugs.python.org/issue10942
    # Workaround is to make sure the bytes are casted to a string.
    return py3compat.decode(ElementTree.tostring(h), 'utf-8')


def add_prompts(code, first='>>> ', cont='... '):
    """Add prompts to code snippets"""
    new_code = []
    code_list = code.split('\n')
    new_code.append(first + code_list[0])
    for line in code_list[1:]:
        new_code.append(cont + line)
    return '\n'.join(new_code)

    
def strip_dollars(text):
    """
    Remove all dollar symbols from text
    
    Parameters
    ----------
    text : str
        Text to remove dollars from
    """

    return text.strip('$')


files_url_pattern = re.compile(r'(src|href)\=([\'"]?)/?files/')
markdown_url_pattern = re.compile(r'(!?)\[(?P<caption>.*?)\]\(/?files/(?P<location>.*?)\)')

def strip_files_prefix(text):
    """
    Fix all fake URLs that start with `files/`, stripping out the `files/` prefix.
    Applies to both urls (for html) and relative paths (for markdown paths).
    
    Parameters
    ----------
    text : str
        Text in which to replace 'src="files/real...' with 'src="real...'
    """
    cleaned_text = files_url_pattern.sub(r"\1=\2", text)
    cleaned_text = markdown_url_pattern.sub(r'\1[\2](\3)', cleaned_text)
    return cleaned_text


def comment_lines(text, prefix='# '):
    """
    Build a Python comment line from input text.
    
    Parameters
    ----------
    text : str
        Text to comment out.
    prefix : str
        Character to append to the start of each line.
    """
    
    #Replace line breaks with line breaks and comment symbols.
    #Also add a comment symbol at the beginning to comment out
    #the first line.
    return prefix + ('\n'+prefix).join(text.split('\n')) 


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

def ipython2python(code):
    """Transform IPython syntax to pure Python syntax

    Parameters
    ----------

    code : str
        IPython code, to be transformed to pure Python
    """
    shell = InteractiveShell.instance()
    return shell.input_transformer_manager.transform_cell(code)

def posix_path(path):
    """Turn a path into posix-style path/to/etc
    
    Mainly for use in latex on Windows,
    where native Windows paths are not allowed.
    """
    if os.path.sep != '/':
        return path.replace(os.path.sep, '/')
    return path

def path2url(path):
    """Turn a file path into a URL"""
    parts = path.split(os.path.sep)
    return '/'.join(quote(part) for part in parts)

def ascii_only(s):
    """ensure a string is ascii"""
    s = py3compat.cast_unicode(s)
    return s.encode('ascii', 'replace').decode('ascii')

def prevent_list_blocks(s):
    """
    Prevent presence of enumerate or itemize blocks in latex headings cells
    """
    out = re.sub('(^\s*\d*)\.', '\\1\.', s)
    out = re.sub('(^\s*)\-', '\\1\-', out)
    out = re.sub('(^\s*)\+', '\\1\+', out)
    out = re.sub('(^\s*)\*', '\\1\*', out)
    return out
