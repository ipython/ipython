#!python
"""Windows-specific part of the installation"""

import os, sys, shutil

def mkshortcut(target,description,link_file,*args,**kw):
    """make a shortcut if it doesn't exist, and register its creation"""
    
    create_shortcut(target, description, link_file,*args,**kw)
    file_created(link_file)

def install():
    """Routine to be run by the win32 installer with the -install switch."""

    from IPython.Release import version

    # Get some system constants
    prefix = sys.prefix
    python = prefix + r'\python.exe'
    # Lookup path to common startmenu ...
    ip_dir = get_special_folder_path('CSIDL_COMMON_PROGRAMS') + r'\IPython'
    
    # Some usability warnings at installation time.  I don't want them at the
    # top-level, so they don't appear if the user is uninstalling.
    try:
        import ctypes
    except ImportError:
        print ('To take full advantage of IPython, you need ctypes from:\n'
               'http://sourceforge.net/projects/ctypes')

    try:
        import win32con
    except ImportError:
        print ('To take full advantage of IPython, you need pywin32 from:\n'
               'http://starship.python.net/crew/mhammond/win32/Downloads.html')

    try:
        import readline
    except ImportError:
        print ('To take full advantage of IPython, you need readline from:\n'
               'http://sourceforge.net/projects/uncpythontools')

    # Create IPython entry ...
    if not os.path.isdir(ip_dir):
        os.mkdir(ip_dir)
        directory_created(ip_dir)

    # Create program shortcuts ...
    f = ip_dir + r'\IPython.lnk'
    a = prefix + r'\scripts\ipython'
    mkshortcut(python,'IPython',f,a)

    f = ip_dir + r'\pysh.lnk'
    a = prefix + r'\scripts\ipython -p sh'
    mkshortcut(python,'IPython command prompt mode',f,a)

    f = ip_dir + r'\scipy.lnk'
    a = prefix + r'\scripts\ipython -pylab -p sci'
    mkshortcut(python,'IPython scipy profile',f,a)

    # Create documentation shortcuts ...    
    t = prefix + r'\share\doc\ipython-%s\manual.pdf' % version
    f = ip_dir + r'\Manual in PDF.lnk'
    mkshortcut(t,r'IPython Manual - PDF-Format',f)

    t = prefix + r'\share\doc\ipython-%s\manual\manual.html' % version
    f = ip_dir + r'\Manual in HTML.lnk'
    mkshortcut(t,'IPython Manual - HTML-Format',f)

    # make ipython.py
    shutil.copy(prefix + r'\scripts\ipython', prefix + r'\scripts\ipython.py')
    
def remove():
    """Routine to be run by the win32 installer with the -remove switch."""
    pass

# main()
if len(sys.argv) > 1:
    if sys.argv[1] == '-install':
        install()
    elif sys.argv[1] == '-remove':
        remove()
    else:
        print "Script was called with option %s" % sys.argv[1]
