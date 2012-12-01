#!python
"""Distutils post installation script for Windows.

http://docs.python.org/2/distutils/builtdist.html#the-postinstallation-script

"""

from __future__ import print_function

import os
import sys
import shutil
import platform

try:
    import setuptools
    have_setuptools = True
except ImportError:
    have_setuptools = False


pjoin = os.path.join

# suffix for start menu folder names
pyver = "(Py%i.%i %i bit)" % (sys.version_info[0], sys.version_info[1],
                              (32, 64)[sys.maxsize > 2**32])


def mkshortcut(target, description, linkdir, arguments="", iconpath='',
               workdir="%HOMEDRIVE%%HOMEPATH%", iconindex=0):
    """Make a shortcut if it doesn't exist and register its creation."""
    filename = pjoin(linkdir, description + '.lnk')
    description = "%s %s" % (description, pyver)
    create_shortcut(target, description, filename, arguments, workdir,
                    iconpath, iconindex)
    file_created(filename)


def arguments(scriptsdir, script, scriptargs=''):
    """Return command line arguments to be passed to the python executable."""
    cmdbase = suffix(pjoin(scriptsdir, script))
    if have_setuptools:
        cmdbase += '-script.py'
    return '"%s" %s' % (cmdbase, scriptargs)


def suffix(s):
    """Add '3' suffix to programs for Python 3."""
    if sys.version_info[0] == 3:
        s = s + '3'
    return s


def install():
    """Routine to be run by the win32 installer with the -install switch."""
    # Get some system constants
    python = pjoin(sys.prefix, 'python.exe')
    pythonw = pjoin(sys.prefix, 'pythonw.exe')

    if not have_setuptools:
        # This currently doesn't work without setuptools,
        # so don't bother making broken links
        print("Distribute (setuptools) is required to"
              " create Start Menu items.", file=sys.stderr)
        print("Re-run this installer after installing"
              " distribute to get Start Menu items.", file=sys.stderr)
        return

    # Lookup path to common startmenu ...
    ip_start_menu = pjoin(get_special_folder_path('CSIDL_COMMON_PROGRAMS'),
                          'IPython %s' % pyver)

    # Create IPython entry ...
    if not os.path.isdir(ip_start_menu):
        os.mkdir(ip_start_menu)
        directory_created(ip_start_menu)

    # Create .py and .bat files to make things available from
    # the Windows command line.  Thanks to the Twisted project
    # for this logic!
    programs = [
        'ipython',
        'iptest',
        'ipcontroller',
        'ipengine',
        'ipcluster',
        'irunner',
    ]
    programs = [suffix(p) for p in programs]
    scripts = pjoin(sys.prefix, 'scripts')
    if not have_setuptools:
        # only create .bat files if we don't have setuptools
        for program in programs:
            raw = pjoin(scripts, program)
            bat = raw + '.bat'
            py = raw + '.py'
            # Create .py versions of the scripts
            shutil.copy(raw, py)
            # Create .bat files for each of the scripts
            bat_file = file(bat, 'w')
            bat_file.write("@%s %s %%*" % (python, py))
            bat_file.close()

    # Create Start Menu shortcuts
    iconpath = pjoin(scripts, 'ipython.ico')
    mkshortcut(python, 'IPython', ip_start_menu,
               arguments(scripts, 'ipython'), iconpath)
    mkshortcut(python, 'IPython (pylab mode)', ip_start_menu,
               arguments(scripts, 'ipython', '--pylab'), iconpath)
    mkshortcut(python, 'IPython Controller', ip_start_menu,
               arguments(scripts, 'ipcontroller'), iconpath)
    mkshortcut(python, 'IPython Engine', ip_start_menu,
               arguments(scripts, 'ipengine'), iconpath)
    mkshortcut(pythonw, 'IPython Qt Console', ip_start_menu,
               arguments(scripts, 'ipython', 'qtconsole'), iconpath)
    mkshortcut(pythonw, 'IPython Qt Console (pylab mode)', ip_start_menu,
               arguments(scripts, 'ipython', 'qtconsole --pylab=inline'),
               iconpath)

    iconpath = pjoin(scripts, 'ipython_nb.ico')
    mkshortcut(python, 'IPython Notebook', ip_start_menu,
               arguments(scripts, 'ipython', 'notebook'), iconpath)
    mkshortcut(python, 'IPython Notebook (pylab mode)', ip_start_menu,
               arguments(scripts, 'ipython', 'notebook --pylab=inline'),
               iconpath)

    try:
        import IPython
        mkshortcut(pythonw, 'IPython Documentation', ip_start_menu,
                   '-m webbrowser -t "http://ipython.org/ipython-doc/'
                   'rel-%s/index.html"' % IPython.__version__,
                   iconpath='url.dll')
    except Exception:
        pass

    # Disable pysh Start item until the profile restores functionality
    # Most of this code is in IPython/deathrow, and needs to be updated
    # to 0.11 APIs
    #mkshortcut(python, 'IPython%s (command prompt mode)', ip_start_menu,
    #           arguments(scripts, 'ipython', 'profile=pysh --init'))


def remove():
    """Routine to be run by the win32 installer with the -remove switch."""
    pass


# main()
if len(sys.argv) > 1:
    if sys.argv[1] == '-install':
        try:
            install()
        except OSError:
            print("Failed to create Start Menu items, try running the"
                  " installer as administrator.", file=sys.stderr)
    elif sys.argv[1] == '-remove':
        remove()
    else:
        print("Script was called with option %s" % sys.argv[1],
              file=sys.stderr)
