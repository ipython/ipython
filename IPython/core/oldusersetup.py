# -*- coding: utf-8 -*-
"""
Main IPython Component
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2001 Janko Hauser <jhauser@zscout.de>
#  Copyright (C) 2001-2007 Fernando Perez. <fperez@colorado.edu>
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import glob
import os
import shutil
import sys

from IPython.utils.genutils import *

def user_setup(ipythondir,rc_suffix,mode='install',interactive=True):
    """Install or upgrade the user configuration directory.

    Can be called when running for the first time or to upgrade the user's
    .ipython/ directory.

    Parameters
    ----------
      ipythondir : path
        The directory to be used for installation/upgrade.  In 'install' mode,
        if this path already exists, the function exits immediately.

      rc_suffix : str
        Extension for the config files.  On *nix platforms it is typically the
        empty string, while Windows normally uses '.ini'.

      mode : str, optional
        Valid modes are 'install' and 'upgrade'.

      interactive : bool, optional
        If False, do not wait for user input on any errors.  Normally after
        printing its status information, this function waits for the user to
        hit Return before proceeding.  This is because the default use case is
        when first installing the IPython configuration, so we want the user to
        acknowledge the initial message, which contains some useful
        information.
        """

    # For automatic use, deactivate all i/o
    if interactive:
        def wait():
            try:
                raw_input("Please press <RETURN> to start IPython.")
            except EOFError:
                print >> Term.cout
            print '*'*70

        def printf(s):
            print s
    else:
        wait = lambda : None
        printf = lambda s : None

    # Install mode should be re-entrant: if the install dir already exists,
    # bail out cleanly.
    # XXX.  This is too hasty to return.  We need to check to make sure that
    # all the expected config files and directories are actually there. We
    # currently have a failure mode if someone deletes a needed config file
    # but still has the ipythondir.
    if mode == 'install' and os.path.isdir(ipythondir):
        return

    cwd = os.getcwd()  # remember where we started
    glb = glob.glob

    printf('*'*70)
    if mode == 'install':
        printf(
"""Welcome to IPython. I will try to create a personal configuration directory
where you can customize many aspects of IPython's functionality in:\n""")
    else:
        printf('I am going to upgrade your configuration in:')

    printf(ipythondir)

    rcdirend = os.path.join('IPython','config','userconfig')
    cfg = lambda d: os.path.join(d,rcdirend)
    try:
        rcdir = filter(os.path.isdir,map(cfg,sys.path))[0]
        printf("Initializing from configuration: %s" % rcdir)
    except IndexError:
        warning = """
Installation error. IPython's directory was not found.

Check the following:

The ipython/IPython directory should be in a directory belonging to your
PYTHONPATH environment variable (that is, it should be in a directory
belonging to sys.path). You can copy it explicitly there or just link to it.

IPython will create a minimal default configuration for you.

"""
        warn(warning)
        wait()

        if sys.platform =='win32':
            inif = 'ipythonrc.ini'
        else:
            inif = 'ipythonrc'
        minimal_setup = {'ipy_user_conf.py' : 'import ipy_defaults',
                         inif : '# intentionally left blank' }
        os.makedirs(ipythondir, mode = 0777)
        for f, cont in minimal_setup.items():
            # In 2.5, this can be more cleanly done using 'with'
            fobj = file(ipythondir + '/' + f,'w')
            fobj.write(cont)
            fobj.close()

        return

    if mode == 'install':
        try:
            shutil.copytree(rcdir,ipythondir)
            os.chdir(ipythondir)
            rc_files = glb("ipythonrc*")
            for rc_file in rc_files:
                os.rename(rc_file,rc_file+rc_suffix)
        except:
            warning = """

There was a problem with the installation:
%s
Try to correct it or contact the developers if you think it's a bug.
IPython will proceed with builtin defaults.""" % sys.exc_info()[1]
            warn(warning)
            wait()
            return

    elif mode == 'upgrade':
        try:
            os.chdir(ipythondir)
        except:
            printf("""
Can not upgrade: changing to directory %s failed. Details:
%s
""" % (ipythondir,sys.exc_info()[1]) )
            wait()
            return
        else:
            sources = glb(os.path.join(rcdir,'[A-Za-z]*'))
            for new_full_path in sources:
                new_filename = os.path.basename(new_full_path)
                if new_filename.startswith('ipythonrc'):
                    new_filename = new_filename + rc_suffix
                # The config directory should only contain files, skip any
                # directories which may be there (like CVS)
                if os.path.isdir(new_full_path):
                    continue
                if os.path.exists(new_filename):
                    old_file = new_filename+'.old'
                    if os.path.exists(old_file):
                        os.remove(old_file)
                    os.rename(new_filename,old_file)
                shutil.copy(new_full_path,new_filename)
    else:
        raise ValueError('unrecognized mode for install: %r' % mode)

    # Fix line-endings to those native to each platform in the config
    # directory.
    try:
        os.chdir(ipythondir)
    except:
        printf("""
Problem: changing to directory %s failed.
Details:
%s

Some configuration files may have incorrect line endings.  This should not
cause any problems during execution.  """ % (ipythondir,sys.exc_info()[1]) )
        wait()
    else:
        for fname in glb('ipythonrc*'):
            try:
                native_line_ends(fname,backup=0)
            except IOError:
                pass

    if mode == 'install':
        printf("""
Successful installation!

Please read the sections 'Initial Configuration' and 'Quick Tips' in the
IPython manual (there are both HTML and PDF versions supplied with the
distribution) to make sure that your system environment is properly configured
to take advantage of IPython's features.

Important note: the configuration system has changed! The old system is
still in place, but its setting may be partly overridden by the settings in 
"~/.ipython/ipy_user_conf.py" config file. Please take a look at the file 
if some of the new settings bother you. 

""")
    else:
        printf("""
Successful upgrade!

All files in your directory:
%(ipythondir)s
which would have been overwritten by the upgrade were backed up with a .old
extension.  If you had made particular customizations in those files you may
want to merge them back into the new files.""" % locals() )
    wait()
    os.chdir(cwd)