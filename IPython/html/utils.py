"""Notebook related utilities

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from __future__ import print_function

import os
import stat

try:
    from urllib.parse import quote, unquote
except ImportError:
    from urllib import quote, unquote

from IPython.utils import py3compat

# UF_HIDDEN is a stat flag not defined in the stat module.
# It is used by BSD to indicate hidden files.
UF_HIDDEN = getattr(stat, 'UF_HIDDEN', 32768)

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

def url_path_join(*pieces):
    """Join components of url into a relative url

    Use to prevent double slash when joining subpath. This will leave the
    initial and final / in place
    """
    initial = pieces[0].startswith('/')
    final = pieces[-1].endswith('/')
    stripped = [s.strip('/') for s in pieces]
    result = '/'.join(s for s in stripped if s)
    if initial: result = '/' + result
    if final: result = result + '/'
    if result == '//': result = '/'
    return result

def path2url(path):
    """Convert a local file path to a URL"""
    pieces = [ quote(p) for p in path.split(os.sep) ]
    # preserve trailing /
    if pieces[-1] == '':
        pieces[-1] = '/'
    url = url_path_join(*pieces)
    return url

def url2path(url):
    """Convert a URL to a local file path"""
    pieces = [ unquote(p) for p in url.split('/') ]
    path = os.path.join(*pieces)
    return path
    
def url_escape(path):
    """Escape special characters in a URL path
    
    Turns '/foo bar/' into '/foo%20bar/'
    """
    parts = py3compat.unicode_to_str(path).split('/')
    return u'/'.join([quote(p) for p in parts])

def url_unescape(path):
    """Unescape special characters in a URL path
    
    Turns '/foo%20bar/' into '/foo bar/'
    """
    return u'/'.join([
        py3compat.str_to_unicode(unquote(p))
        for p in py3compat.unicode_to_str(path).split('/')
    ])

def is_hidden(absolute_root, absolute_path):
    """Is a file is hidden or contained in a hidden directory.
    
    Hidden is determined by either name starting with '.' or the UF_HIDDEN
    flag as reported by stat.
    
    Parameters
    ----------
    absolute_root : unicode
    absolute_path : unicode
    """
    inside_root = absolute_path[len(absolute_root):]
    if any(part.startswith('.') for part in inside_root.split(os.sep)):
        return True
    
    # check UF_HIDDEN on any location up to root
    path = absolute_path
    while path and path.startswith(absolute_root) and path != absolute_root:
        st = os.stat(path)
        if getattr(st, 'st_flags', 0) & UF_HIDDEN:
            return True
        path = os.path.dirname(path)

    return False

