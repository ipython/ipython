Notes for Windows Users
=======================

See http://ipython.scipy.org/moin/IpythonOnWindows for up-to-date information
about running IPython on Windows.


Requirements
------------

IPython runs under (as far as the Windows family is concerned):

- Windows XP, 2000 (and probably WinNT): works well.  It needs:

  * PyWin32: http://sourceforge.net/projects/pywin32/

  * PyReadline: http://ipython.scipy.org/moin/PyReadline/Intro
    
  * If you are using Python2.4, this in turn requires Tomas Heller's ctypes
    from: http://starship.python.net/crew/theller/ctypes (not needed for Python
    2.5 users, since 2.5 already ships with ctypes).

- Windows 95/98/ME: I have no idea. It should work, but I can't test.

- CygWin environments should work, they are basically Posix.

It needs Python 2.3 or newer.


Installation
------------

Double-click the supplied .exe installer file. If all goes well, that's all
you need to do. You should now have an IPython entry in your Start Menu.


Installation from source distribution
-------------------------------------

In case the automatic installer does not work for some reason, you can
download the ipython-XXX.tar.gz file, which contains the full IPython source
distribution (the popular WinZip can read .tar.gz files). 

After uncompressing the archive, you can install it at a command terminal just 
like any other Python module, by using python setup.py install'. After this 
completes, you can run the supplied win32_manual_post_install.py script which 
will add the relevant shortcuts to your startup menu.

Optionally, you may skip installation altogether and just launch "ipython.py" 
from the root folder of the extracted source distribution.
