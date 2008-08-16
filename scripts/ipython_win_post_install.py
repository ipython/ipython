#!python
"""Windows-specific part of the installation"""

import os, sys, shutil
pjoin = os.path.join

def mkshortcut(target,description,link_file,*args,**kw):
    """make a shortcut if it doesn't exist, and register its creation"""
    
    create_shortcut(target, description, link_file,*args,**kw)
    file_created(link_file)

def install():
    """Routine to be run by the win32 installer with the -install switch."""
    
    from IPython.Release import version
    
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
               'https://launchpad.net/pyreadline')
    
    # Get some system constants
    prefix = sys.prefix
    python = pjoin(prefix, 'python.exe')
    
    # Lookup path to common startmenu ...
    ip_start_menu = pjoin(get_special_folder_path('CSIDL_COMMON_PROGRAMS'), 'IPython')
    # Create IPython entry ...
    if not os.path.isdir(ip_start_menu):
        os.mkdir(ip_start_menu)
        directory_created(ip_start_menu)
    
    # Create .py and .bat files to make things available from
    # the Windows command line
    programs = 'ipython iptest ipcontroller ipengine ipcluster'
    scripts = pjoin(prefix,'scripts')
    for program in programs.split():
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
    ipybase = '"' + prefix + r'\scripts\ipython"'    

    # Create program shortcuts ...
    f = ip_start_menu + r'\IPython.lnk'
    a = ipybase
    mkshortcut(python,'IPython',f,a)
    
    f = ip_start_menu + r'\pysh.lnk'
    a = ipybase+' -p sh'
    mkshortcut(python,'IPython (command prompt mode)',f,a)
    
    f = ip_start_menu + r'\pylab.lnk'
    a = ipybase+' -pylab'
    mkshortcut(python,'IPython (PyLab mode)',f,a)
    
    f = ip_start_menu + r'\scipy.lnk'
    a = ipybase+' -pylab -p scipy'
    mkshortcut(python,'IPython (scipy profile)',f,a)
    
    # Create documentation shortcuts ...
    t = prefix + r'\share\doc\ipython\manual\ipython.pdf'
    f = ip_start_menu + r'\Manual in PDF.lnk'
    mkshortcut(t,r'IPython Manual - PDF-Format',f)
    
    t = prefix + r'\share\doc\ipython\manual\html\index.html'
    f = ip_start_menu + r'\Manual in HTML.lnk'
    mkshortcut(t,'IPython Manual - HTML-Format',f)
    
    
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
