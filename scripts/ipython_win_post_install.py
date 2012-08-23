#!python
"""Windows-specific part of the installation"""

from __future__ import print_function

import os, sys, shutil
pjoin = os.path.join

# import setuptools if we can
try:
    import setuptools
except ImportError:
    pass


def mkshortcut(target,description,link_file,*args,**kw):
    """make a shortcut if it doesn't exist, and register its creation"""
    
    create_shortcut(target, description, link_file,*args,**kw)
    file_created(link_file)

def suffix(s):
    """add '3' suffix to programs for Python 3"""
    if sys.version_info[0] == 3:
        s = s+'3'
    return s

def install():
    """Routine to be run by the win32 installer with the -install switch."""
    
    # Get some system constants
    prefix = sys.prefix
    python = pjoin(prefix, 'python.exe')
    pythonw = pjoin(prefix, 'pythonw.exe')
    have_setuptools = 'setuptools' in sys.modules
    
    if not have_setuptools:
        # This currently doesn't work without setuptools,
        # so don't bother making broken links
        print("Distribute (setuptools) is required to create Start Menu items.", file=sys.stderr)
        print("Re-run this installer after installing distribute to get Start Menu items.", file=sys.stderr)
        return
    
    # Lookup path to common startmenu ...
    ip_start_menu = pjoin(get_special_folder_path('CSIDL_COMMON_PROGRAMS'),
                          'IPython (Py%i.%i %i bit)' % (sys.version_info[0],
                                                        sys.version_info[1],
                                                        8*tuple.__itemsize__))
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
        'irunner'
    ]
    programs = [ suffix(p) for p in programs ]
    scripts = pjoin(prefix,'scripts')
    if not have_setuptools:
        # only create .bat files if we don't have setuptools
        for program in programs:
            raw = pjoin(scripts, program)
            bat = raw + '.bat'
            py = raw + '.py'
            # Create .py versions of the scripts
            shutil.copy(raw, py)
            # Create .bat files for each of the scripts
            bat_file = file(bat,'w')
            bat_file.write("@%s %s %%*" % (python, py))
            bat_file.close()

    # Now move onto setting the Start Menu up
    ipybase = suffix(pjoin(scripts, 'ipython'))
    if have_setuptools:
        # let setuptools take care of the scripts:
        ipybase = ipybase + '-script.py'
    workdir = "%HOMEDRIVE%%HOMEPATH%"

    link = pjoin(ip_start_menu, 'IPython.lnk')
    cmd = '"%s"' % ipybase
    mkshortcut(python, 'IPython', link, cmd, workdir)
    
    # Disable pysh Start item until the profile restores functionality
    # Most of this code is in IPython/deathrow, and needs to be updated
    # to 0.11 APIs
    
    # link = pjoin(ip_start_menu, 'pysh.lnk')
    # cmd = '"%s" profile=pysh --init' % ipybase
    # mkshortcut(python, 'IPython (command prompt mode)', link, cmd, workdir)
    
    link = pjoin(ip_start_menu, 'pylab.lnk')
    cmd = '"%s" --pylab' % ipybase
    mkshortcut(python, 'IPython (pylab mode)', link, cmd, workdir)
        
    link = pjoin(ip_start_menu, 'ipcontroller.lnk')
    cmdbase = suffix(pjoin(scripts, 'ipcontroller'))
    if have_setuptools:
        cmdbase += '-script.py'
    cmd = '"%s"' % cmdbase
    mkshortcut(python, 'IPython controller', link, cmd, workdir)
    
    link = pjoin(ip_start_menu, 'ipengine.lnk')
    cmdbase = suffix(pjoin(scripts, 'ipengine'))
    if have_setuptools:
        cmdbase += '-script.py'
    cmd = '"%s"' % cmdbase
    mkshortcut(python, 'IPython engine', link, cmd, workdir)

    link = pjoin(ip_start_menu, 'ipythonqt.lnk')
    cmdbase = suffix(pjoin(scripts, 'ipython'))
    if have_setuptools:
        cmdbase += '-script.py'
    cmd = '"%s" qtconsole' % cmdbase
    mkshortcut(pythonw, 'IPython Qt Console', link, cmd, workdir)

    # FIXME: These below are commented out because we don't ship the html built
    # docs anymore.  We should make the shortcut to continue existing, but as a
    # URL to the online the docs for the right version of IPython.  The stable
    # URLs have the pattern:
    # http://ipython.org/ipython-doc/rel-X.Y.Z/html
    # For IPython version X.Y.Z.
    
    ## # Create documentation shortcuts ...
    ## t = prefix + r'\share\doc\ipython\manual\index.html'
    ## f = ip_start_menu + r'\Manual in HTML.lnk'
    ## mkshortcut(t,'IPython Manual - HTML-Format',f)
    
def remove():
    """Routine to be run by the win32 installer with the -remove switch."""
    pass


# main()
if len(sys.argv) > 1:
    if sys.argv[1] == '-install':
        try:
            install()
        except OSError:
            print("Failed to create Start Menu items, try running installer as administrator.", file=sys.stderr)
    elif sys.argv[1] == '-remove':
        remove()
    else:
        print("Script was called with option %s" % sys.argv[1], file=sys.stderr)
