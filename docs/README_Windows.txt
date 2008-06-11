Notes for Windows Users
=======================

These are just minimal notes.  The manual contains more detailed
information.

Requirements
------------

IPython runs under (as far as the Windows family is concerned):

- Windows XP (I think WinNT/2000 are ok): works well.  It needs:

  * Gary Bishop's readline from 
    http://sourceforge.net/projects/uncpythontools.
    
  * This in turn requires Tomas Heller's ctypes from
    http://starship.python.net/crew/theller/ctypes.

- Windows 95/98/ME: I have no idea. It should work, but I can't test.

- CygWin environments should work, they are basically Posix.

It needs Python 2.2 or newer.


Installation
------------

Double-click the supplied .exe installer file.  If all goes well, that's all
you need to do. You should now have an IPython entry in your Start Menu.

In case the automatic installer does not work for some reason, you can
download the ipython-XXX.tar.gz file, which contains the full IPython source
distribution (the popular WinZip can read .tar.gz files). After uncompressing
the archive, you can install it at a command terminal just like any other
Python module, by using python setup.py install'. After this completes, you
can run the supplied win32_manual_post_install.py script which will add
the relevant shortcuts to your startup menu.
