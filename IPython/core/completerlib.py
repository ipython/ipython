"""Implementations for various useful completers.

These are all loaded by default by IPython.
"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import glob
import inspect
import os
import re
import sys

# Third-party imports
from time import time
from zipimport import zipimporter

# Our own imports
from IPython.core.completer import expand_user, compress_user
from IPython.core.error import TryNext
from IPython.utils import py3compat
from IPython.utils._process_common import arg_split

# FIXME: this should be pulled in with the right call via the component system
from IPython.core.ipapi import get as get_ipython

#-----------------------------------------------------------------------------
# Globals and constants
#-----------------------------------------------------------------------------

# Time in seconds after which the rootmodules will be stored permanently in the
# ipython ip.db database (kept in the user's .ipython dir).
TIMEOUT_STORAGE = 2

# Time in seconds after which we give up
TIMEOUT_GIVEUP = 20

# Regular expression for the python import statement
import_re = re.compile(r'.*(\.so|\.py[cod]?)$')

# RE for the ipython %run command (python + ipython scripts)
magic_run_re = re.compile(r'.*(\.ipy|\.py[w]?)$')

#-----------------------------------------------------------------------------
# Local utilities
#-----------------------------------------------------------------------------

def module_list(path):
    """
    Return the list containing the names of the modules available in the given
    folder.
    """

    if os.path.isdir(path):
        folder_list = os.listdir(path)
    elif path.endswith('.egg'):
        try:
            folder_list = [f for f in zipimporter(path)._files]
        except:
            folder_list = []
    else:
        folder_list = []

    if not folder_list:
        return []

    # A few local constants to be used in loops below
    isfile = os.path.isfile
    pjoin = os.path.join
    basename = os.path.basename

    # Now find actual path matches for packages or modules
    folder_list = [p for p in folder_list
                   if isfile(pjoin(path, p,'__init__.py'))
                   or import_re.match(p) ]

    return [basename(p).split('.')[0] for p in folder_list]

def get_root_modules():
    """
    Returns a list containing the names of all the modules available in the
    folders of the pythonpath.
    """
    ip = get_ipython()

    if 'rootmodules' in ip.db:
        return ip.db['rootmodules']

    t = time()
    store = False
    modules = list(sys.builtin_module_names)
    for path in sys.path:
        modules += module_list(path)
        if time() - t >= TIMEOUT_STORAGE and not store:
            store = True
            print("\nCaching the list of root modules, please wait!")
            print("(This will only be done once - type '%rehashx' to "
                  "reset cache!)\n")
            sys.stdout.flush()
        if time() - t > TIMEOUT_GIVEUP:
            print("This is taking too long, we give up.\n")
            ip.db['rootmodules'] = []
            return []

    modules = set(modules)
    if '__init__' in modules:
        modules.remove('__init__')
    modules = list(modules)
    if store:
        ip.db['rootmodules'] = modules
    return modules


def is_importable(module, attr, only_modules):
    if only_modules:
        return inspect.ismodule(getattr(module, attr))
    else:
        return not(attr[:2] == '__' and attr[-2:] == '__')


def try_import(mod, only_modules=False):
    try:
        m = __import__(mod)
    except:
        return []
    mods = mod.split('.')
    for module in mods[1:]:
        m = getattr(m, module)

    m_is_init = hasattr(m, '__file__') and '__init__' in m.__file__

    completions = []
    if (not hasattr(m, '__file__')) or (not only_modules) or m_is_init:
        completions.extend( [attr for attr in dir(m) if
                             is_importable(m, attr, only_modules)])

    completions.extend(getattr(m, '__all__', []))
    if m_is_init:
        completions.extend(module_list(os.path.dirname(m.__file__)))
    completions = set(completions)
    if '__init__' in completions:
        completions.remove('__init__')
    return list(completions)


#-----------------------------------------------------------------------------
# Completion-related functions.
#-----------------------------------------------------------------------------

def quick_completer(cmd, completions):
    """ Easily create a trivial completer for a command.

    Takes either a list of completions, or all completions in string (that will
    be split on whitespace).

    Example::

        [d:\ipython]|1> import ipy_completers
        [d:\ipython]|2> ipy_completers.quick_completer('foo', ['bar','baz'])
        [d:\ipython]|3> foo b<TAB>
        bar baz
        [d:\ipython]|3> foo ba
    """

    if isinstance(completions, basestring):
        completions = completions.split()

    def do_complete(self, event):
        return completions

    get_ipython().set_hook('complete_command',do_complete, str_key = cmd)


def module_completion(line):
    """
    Returns a list containing the completion possibilities for an import line.

    The line looks like this :
    'import xml.d'
    'from xml.dom import'
    """

    words = line.split(' ')
    nwords = len(words)

    # from whatever <tab> -> 'import '
    if nwords == 3 and words[0] == 'from':
        return ['import ']

    # 'from xy<tab>' or 'import xy<tab>'
    if nwords < 3 and (words[0] in ['import','from']) :
        if nwords == 1:
            return get_root_modules()
        mod = words[1].split('.')
        if len(mod) < 2:
            return get_root_modules()
        completion_list = try_import('.'.join(mod[:-1]), True)
        return ['.'.join(mod[:-1] + [el]) for el in completion_list]

    # 'from xyz import abc<tab>'
    if nwords >= 3 and words[0] == 'from':
        mod = words[1]
        return try_import(mod)

#-----------------------------------------------------------------------------
# Completers
#-----------------------------------------------------------------------------
# These all have the func(self, event) signature to be used as custom
# completers

def module_completer(self,event):
    """Give completions after user has typed 'import ...' or 'from ...'"""

    # This works in all versions of python.  While 2.5 has
    # pkgutil.walk_packages(), that particular routine is fairly dangerous,
    # since it imports *EVERYTHING* on sys.path.  That is: a) very slow b) full
    # of possibly problematic side effects.
    # This search the folders in the sys.path for available modules.

    return module_completion(event.line)

# FIXME: there's a lot of logic common to the run, cd and builtin file
# completers, that is currently reimplemented in each.

def magic_run_completer(self, event):
    """Complete files that end in .py or .ipy for the %run command.
    """
    comps = arg_split(event.line, strict=False)
    relpath = (len(comps) > 1 and comps[-1] or '').strip("'\"")

    #print("\nev=", event)  # dbg
    #print("rp=", relpath)  # dbg
    #print('comps=', comps)  # dbg

    lglob = glob.glob
    isdir = os.path.isdir
    relpath, tilde_expand, tilde_val = expand_user(relpath)

    dirs = [f.replace('\\','/') + "/" for f in lglob(relpath+'*') if isdir(f)]

    # Find if the user has already typed the first filename, after which we
    # should complete on all files, since after the first one other files may
    # be arguments to the input script.

    if filter(magic_run_re.match, comps):
        pys =  [f.replace('\\','/') for f in lglob('*')]
    else:
        pys =  [f.replace('\\','/')
                for f in lglob(relpath+'*.py') + lglob(relpath+'*.ipy') +
                lglob(relpath + '*.pyw')]
    #print('run comp:', dirs+pys) # dbg
    return [compress_user(p, tilde_expand, tilde_val) for p in dirs+pys]


def cd_completer(self, event):
    """Completer function for cd, which only returns directories."""
    ip = get_ipython()
    relpath = event.symbol

    #print(event) # dbg
    if event.line.endswith('-b') or ' -b ' in event.line:
        # return only bookmark completions
        bkms = self.db.get('bookmarks', None)
        if bkms:
            return bkms.keys()
        else:
            return []

    if event.symbol == '-':
        width_dh = str(len(str(len(ip.user_ns['_dh']) + 1)))
        # jump in directory history by number
        fmt = '-%0' + width_dh +'d [%s]'
        ents = [ fmt % (i,s) for i,s in enumerate(ip.user_ns['_dh'])]
        if len(ents) > 1:
            return ents
        return []

    if event.symbol.startswith('--'):
        return ["--" + os.path.basename(d) for d in ip.user_ns['_dh']]

    # Expand ~ in path and normalize directory separators.
    relpath, tilde_expand, tilde_val = expand_user(relpath)
    relpath = relpath.replace('\\','/')

    found = []
    for d in [f.replace('\\','/') + '/' for f in glob.glob(relpath+'*')
              if os.path.isdir(f)]:
        if ' ' in d:
            # we don't want to deal with any of that, complex code
            # for this is elsewhere
            raise TryNext

        found.append(d)

    if not found:
        if os.path.isdir(relpath):
            return [compress_user(relpath, tilde_expand, tilde_val)]

        # if no completions so far, try bookmarks
        bks = self.db.get('bookmarks',{}).iterkeys()
        bkmatches = [s for s in bks if s.startswith(event.symbol)]
        if bkmatches:
            return bkmatches

        raise TryNext

    return [compress_user(p, tilde_expand, tilde_val) for p in found]
