"""hooks for IPython.

In Python, it is possible to overwrite any method of any object if you really
want to.  But IPython exposes a few 'hooks', methods which are _designed_ to
be overwritten by users for customization purposes.  This module defines the
default versions of all such hooks, which get used by IPython if not
overridden by the user.

hooks are simple functions, but they should be declared with 'self' as their
first argument, because when activated they are registered into IPython as
instance methods.  The self argument will be the IPython running instance
itself, so hooks have full access to the entire IPython object.

If you wish to define a new hook and activate it, you need to put the
necessary code into a python file which can be either imported or execfile()'d
from within your ipythonrc configuration.

For example, suppose that you have a module called 'myiphooks' in your
PYTHONPATH, which contains the following definition:

import os
def calljed(self,filename, linenum):
    "My editor hook calls the jed editor directly."
    print "Calling my own editor, jed ..."
    os.system('jed +%d %s' % (linenum,filename))

You can then execute the following line of code to make it the new IPython
editor hook, after having imported 'myiphooks':

ip_set_hook('editor',myiphooks.calljed)

The ip_set_hook function is put by IPython into the builtin namespace, so it
is always available from all running code.

$Id: hooks.py 535 2005-03-02 08:42:25Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2005 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license
__version__ = Release.version

import os

# List here all the default hooks.  For now it's just the editor, but over
# time we'll move here all the public API for user-accessible things.
__all__ = ['editor']

def editor(self,filename, linenum):
    """Open the default editor at the given filename and linenumber.

    This is IPython's default editor hook, you can use it as an example to
    write your own modified one.  To set your own editor function as the
    new editor hook, call ip_set_hook('editor',yourfunc)."""

    # IPython configures a default editor at startup by reading $EDITOR from
    # the environment, and falling back on vi (unix) or notepad (win32).
    editor = self.rc.editor
    
    # marker for at which line to open the file (for existing objects)
    if linenum is None or editor=='notepad':
        linemark = ''
    else:
        linemark = '+%d' % linenum
    # Call the actual editor
    os.system('%s %s %s' % (editor,linemark,filename))
