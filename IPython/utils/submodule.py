"""utilities for checking submodule status"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2013  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import subprocess
import sys

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

pjoin = os.path.join

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def ipython_parent():
    """return IPython's parent (i.e. root if run from git)"""
    from IPython.utils.path import get_ipython_package_dir
    return os.path.abspath(os.path.dirname(get_ipython_package_dir()))

def ipython_submodules(root):
    """return IPython submodules relative to root"""
    return [
        pjoin(root, 'IPython', 'html', 'static', 'components'),
    ]

def is_repo(d):
    """is d a git repo?"""
    return os.path.exists(pjoin(d, '.git'))

def check_submodule_status(root=None):
    """check submodule status

    Has three return values:

    'missing' - submodules are absent
    'unclean' - submodules have unstaged changes
    'clean' - all submodules are up to date
    """

    if hasattr(sys, "frozen"):
        # frozen via py2exe or similar, don't bother
        return 'clean'

    if not root:
        root = ipython_parent()
    
    if not is_repo(root):
        # not in git, assume clean
        return 'clean'

    submodules = ipython_submodules(root)

    for submodule in submodules:
        if not os.path.exists(submodule):
            return 'missing'
    
    # Popen can't handle unicode cwd on Windows Python 2
    if sys.platform == 'win32' and sys.version_info[0] < 3 \
        and not isinstance(root, bytes):
        root = root.encode(sys.getfilesystemencoding() or 'ascii')
    # check with git submodule status
    proc = subprocess.Popen('git submodule status',
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            cwd=root,
    )
    status, _ = proc.communicate()
    status = status.decode("ascii", "replace")

    for line in status.splitlines():
        if line.startswith('-'):
            return 'missing'
        elif line.startswith('+'):
            return 'unclean'

    return 'clean'

def update_submodules(repo_dir):
    """update submodules in a repo"""
    subprocess.check_call("git submodule init", cwd=repo_dir, shell=True)
    subprocess.check_call("git submodule update --recursive", cwd=repo_dir, shell=True)

