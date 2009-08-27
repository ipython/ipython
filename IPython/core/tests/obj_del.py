"""Test code for https://bugs.launchpad.net/ipython/+bug/239054

WARNING: this script exits IPython!  It MUST be run in a subprocess.

When you run the following script from CPython it prints:
__init__ is here
__del__ is here

and creates the __del__.txt file

When you run it from IPython it prints:
__init__ is here

When you exit() or Exit from IPython neothing is printed and no file is created
(the file thing is to make sure __del__ is really never called and not that
just the output is eaten).

Note that if you call %reset in IPython then everything is Ok.

IPython should do the equivalent of %reset and release all the references it
holds before exit. This behavior is important when working with binding objects
that rely on __del__. If the current behavior has some use case then I suggest
to add a configuration option to IPython to control it.
"""
import sys

class A(object):
    def __del__(self):
        print 'obj_del.py: object A deleted'

a = A()

# Now, we force an exit, the caller will check that the del printout was given
_ip.ask_exit()
