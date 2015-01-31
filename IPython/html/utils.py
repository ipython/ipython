"""Notebook related utilities"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

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
    parts = py3compat.unicode_to_str(path, encoding='utf8').split('/')
    return u'/'.join([quote(p) for p in parts])

def url_unescape(path):
    """Unescape special characters in a URL path
    
    Turns '/foo%20bar/' into '/foo bar/'
    """
    return u'/'.join([
        py3compat.str_to_unicode(unquote(p), encoding='utf8')
        for p in py3compat.unicode_to_str(path, encoding='utf8').split('/')
    ])

def is_hidden(abs_path, abs_root=''):
    """Is a file hidden or contained in a hidden directory?
    
    This will start with the rightmost path element and work backwards to the
    given root to see if a path is hidden or in a hidden directory. Hidden is
    determined by either name starting with '.' or the UF_HIDDEN flag as 
    reported by stat.
    
    Parameters
    ----------
    abs_path : unicode
        The absolute path to check for hidden directories.
    abs_root : unicode
        The absolute path of the root directory in which hidden directories
        should be checked for.
    """
    if not abs_root:
        abs_root = abs_path.split(os.sep, 1)[0] + os.sep
    inside_root = abs_path[len(abs_root):]
    if any(part.startswith('.') for part in inside_root.split(os.sep)):
        return True
    
    # check that dirs can be listed
    # may fail on Windows junctions or non-user-readable dirs
    if os.path.isdir(abs_path):
        try:
            os.listdir(abs_path)
        except OSError:
            return True
    
    # check UF_HIDDEN on any location up to root
    path = abs_path
    while path and path.startswith(abs_root) and path != abs_root:
        if not os.path.exists(path):
            path = os.path.dirname(path)
            continue
        try:
            # may fail on Windows junctions
            st = os.stat(path)
        except OSError:
            return True
        if getattr(st, 'st_flags', 0) & UF_HIDDEN:
            return True
        path = os.path.dirname(path)

    return False

def to_os_path(path, root=''):
    """Convert an API path to a filesystem path
    
    If given, root will be prepended to the path.
    root must be a filesystem path already.
    """
    parts = path.strip('/').split('/')
    parts = [p for p in parts if p != ''] # remove duplicate splits
    path = os.path.join(root, *parts)
    return path

def to_api_path(os_path, root=''):
    """Convert a filesystem path to an API path
    
    If given, root will be removed from the path.
    root must be a filesystem path already.
    """
    if os_path.startswith(root):
        os_path = os_path[len(root):]
    parts = os_path.strip(os.path.sep).split(os.path.sep)
    parts = [p for p in parts if p != ''] # remove duplicate splits
    path = '/'.join(parts)
    return path

