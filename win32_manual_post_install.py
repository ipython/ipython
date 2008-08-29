#!python
"""Windows-specific part of the installation"""

import os, sys

try:
    import shutil,pythoncom
    from win32com.shell import shell
    import _winreg as wreg
except ImportError:
    print """
You seem to be missing the PythonWin extensions necessary for automatic
installation.  You can get them (free) from
http://starship.python.net/crew/mhammond/

Please see the manual for details if you want to finish the installation by
hand, or get PythonWin and repeat the procedure.

Press <Enter> to exit this installer."""
    raw_input()
    sys.exit()


def make_shortcut(fname,target,args='',start_in='',comment='',icon=None):
    """Make a Windows shortcut (.lnk) file.

    make_shortcut(fname,target,args='',start_in='',comment='',icon=None)

    Arguments:
        fname - name of the final shortcut file (include the .lnk)
        target - what the shortcut will point to
        args - additional arguments to pass to the target program
        start_in - directory where the target command will be called
        comment - for the popup tooltips
        icon - optional icon file. This must be a tuple of the type 
        (icon_file,index), where index is the index of the icon you want
        in the file. For single .ico files, index=0, but for icon libraries
        contained in a single file it can be >0.
    """

    shortcut = pythoncom.CoCreateInstance(
        shell.CLSID_ShellLink, None,
        pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink
    )
    shortcut.SetPath(target)
    shortcut.SetArguments(args)
    shortcut.SetWorkingDirectory(start_in)
    shortcut.SetDescription(comment)
    if icon:
        shortcut.SetIconLocation(*icon)
    shortcut.QueryInterface(pythoncom.IID_IPersistFile).Save(fname,0)


def run(wait=0):
    # Find where the Start Menu and My Documents are on the filesystem
    key = wreg.OpenKey(wreg.HKEY_CURRENT_USER,
                       r'Software\Microsoft\Windows\CurrentVersion'
                       r'\Explorer\Shell Folders')

    programs_dir = wreg.QueryValueEx(key,'Programs')[0]
    my_documents_dir = wreg.QueryValueEx(key,'Personal')[0]
    key.Close()

    # Find where the 'program files' directory is
    key = wreg.OpenKey(wreg.HKEY_LOCAL_MACHINE,
                       r'SOFTWARE\Microsoft\Windows\CurrentVersion')

    program_files_dir = wreg.QueryValueEx(key,'ProgramFilesDir')[0]
    key.Close()


    # File and directory names
    ip_dir = program_files_dir + r'\IPython'
    ip_prog_dir = programs_dir + r'\IPython'
    doc_dir = ip_dir+r'\docs'
    ip_filename = ip_dir+r'\IPython_shell.py'
    pycon_icon = doc_dir+r'\pycon.ico'

    if not os.path.isdir(ip_dir):
        os.mkdir(ip_dir)

    # Copy startup script and documentation
    shutil.copy(sys.prefix+r'\Scripts\ipython',ip_filename)
    if os.path.isdir(doc_dir):
        shutil.rmtree(doc_dir)
    shutil.copytree('docs',doc_dir)

    # make shortcuts for IPython, html and pdf docs.
    print 'Making entries for IPython in Start Menu...',

    # Create .bat file in \Scripts
    fic = open(sys.prefix + r'\Scripts\ipython.bat','w')
    fic.write('"' + sys.prefix + r'\python.exe' + '" -i ' + '"' +
              sys.prefix + r'\Scripts\ipython" %*')
    fic.close()

    # Create .bat file in \\Scripts
    fic = open(sys.prefix + '\\Scripts\\ipython.bat','w')
    fic.write('"' + sys.prefix + '\\python.exe' + '" -i ' + '"' + sys.prefix + '\\Scripts\ipython" %*')
    fic.close()

    # Create shortcuts in Programs\IPython:
    if not os.path.isdir(ip_prog_dir):
        os.mkdir(ip_prog_dir)
    os.chdir(ip_prog_dir)

    man_pdf = doc_dir + r'\dist\ipython.pdf'
    man_htm = doc_dir + r'\dist\index.html'

    make_shortcut('IPython.lnk',sys.executable, '"%s"' % ip_filename,
                  my_documents_dir,
                  'IPython - Enhanced python command line interpreter',
                  (pycon_icon,0))
    make_shortcut('pysh.lnk',sys.executable, '"%s" -p pysh' % ip_filename,
                  my_documents_dir,
                  'pysh - a system shell with Python syntax (IPython based)',
                  (pycon_icon,0))
    make_shortcut('Manual in HTML format.lnk',man_htm,'','',
                  'IPython Manual - HTML format')
    make_shortcut('Manual in PDF format.lnk',man_pdf,'','',
                  'IPython Manual - PDF format')

    print """Done.

I created the directory %s. There you will find the
IPython startup script and manuals.

An IPython menu was also created in your Start Menu, with entries for
IPython itself and the manual in HTML and PDF formats.

For reading PDF documents you need the freely available Adobe Acrobat
Reader. If you don't have it, you can download it from:
http://www.adobe.com/products/acrobat/readstep2.html
""" % ip_dir

    if wait:
        print "Finished with IPython installation. Press Enter to exit this installer.",
        raw_input()

if __name__ == '__main__':
    run()
