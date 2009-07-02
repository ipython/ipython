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
    # the Windows command line.  Thanks to the Twisted project
    # for this logic!
    programs = [
        'ipython',
        'iptest',
        'ipcontroller',
        'ipengine',
        'ipcluster',
        'ipythonx',
        'ipython-wx',
        'irunner'
    ]
    scripts = pjoin(prefix,'scripts')
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
    ipybase = pjoin(scripts, 'ipython')

    link = pjoin(ip_start_menu, 'IPython.lnk')
    cmd = '"%s"' % ipybase
    mkshortcut(python,'IPython',link,cmd)
    
    link = pjoin(ip_start_menu, 'pysh.lnk')
    cmd = '"%s" -p sh' % ipybase
    mkshortcut(python,'IPython (command prompt mode)',link,cmd)
    
    link = pjoin(ip_start_menu, 'pylab.lnk')
    cmd = '"%s" -pylab' % ipybase
    mkshortcut(python,'IPython (PyLab mode)',link,cmd)
    
    link = pjoin(ip_start_menu, 'scipy.lnk')
    cmd = '"%s" -pylab -p scipy' % ipybase
    mkshortcut(python,'IPython (scipy profile)',link,cmd)
    
    link = pjoin(ip_start_menu, 'IPython test suite.lnk')
    cmd = '"%s" -vv' % pjoin(scripts, 'iptest')
    mkshortcut(python,'Run the IPython test suite',link,cmd)
    
    link = pjoin(ip_start_menu, 'ipcontroller.lnk')
    cmd = '"%s" -xy' % pjoin(scripts, 'ipcontroller')
    mkshortcut(python,'IPython controller',link,cmd)
    
    link = pjoin(ip_start_menu, 'ipengine.lnk')
    cmd = '"%s"' % pjoin(scripts, 'ipengine')
    mkshortcut(python,'IPython engine',link,cmd)
    
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
