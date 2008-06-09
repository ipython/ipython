# encoding: utf-8

"""Foolscap related utilities."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os

from foolscap import Tub, UnauthenticatedTub

def check_furl_file_security(furl_file, secure):
    """Remove the old furl_file if changing security modes."""
    
    if os.path.isfile(furl_file):
        f = open(furl_file, 'r')
        oldfurl = f.read().strip()
        f.close()
        if (oldfurl.startswith('pb://') and not secure) or (oldfurl.startswith('pbu://') and secure):
            os.remove(furl_file)

def is_secure(furl):
    if is_valid(furl):
        if furl.startswith("pb://"):
            return True
        elif furl.startswith("pbu://"):
            return False
    else:
        raise ValueError("invalid furl: %s" % furl)

def is_valid(furl):
    if isinstance(furl, str):
        if furl.startswith("pb://") or furl.startswith("pbu://"):
            return True
    else:
        return False

def find_furl(furl_or_file):
    if isinstance(furl_or_file, str):
        if is_valid(furl_or_file):
            return furl_or_file
    if os.path.isfile(furl_or_file):
        furl = open(furl_or_file, 'r').read().strip()
        if is_valid(furl):
            return furl
    raise ValueError("not a furl or a file containing a furl: %s" % furl_or_file)

# We do this so if a user doesn't have OpenSSL installed, it will try to use
# an UnauthenticatedTub.  But, they will still run into problems if they
# try to use encrypted furls.
try:
    import OpenSSL
except:
    Tub = UnauthenticatedTub
    have_crypto = False
else:
    have_crypto = True


