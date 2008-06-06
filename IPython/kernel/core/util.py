# encoding: utf-8

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os
import sys


# This class is mostly taken from IPython.
class InputList(list):
    """ Class to store user input.

    It's basically a list, but slices return a string instead of a list, thus
    allowing things like (assuming 'In' is an instance):

    exec In[4:7]

    or

    exec In[5:9] + In[14] + In[21:25]
    """

    def __getslice__(self, i, j):
        return ''.join(list.__getslice__(self, i, j))

    def add(self, index, command):
        """ Add a command to the list with the appropriate index.

        If the index is greater than the current length of the list, empty
        strings are added in between.
        """

        length = len(self)
        if length == index:
            self.append(command)
        elif length > index:
            self[index] = command
        else:
            extras = index - length
            self.extend([''] * extras)
            self.append(command)


class Bunch(dict):
    """ A dictionary that exposes its keys as attributes.
    """

    def __init__(self, *args, **kwds):
        dict.__init__(self, *args, **kwds)
        self.__dict__ = self


def esc_quotes(strng):
    """ Return the input string with single and double quotes escaped out.
    """

    return strng.replace('"', '\\"').replace("'", "\\'")

def make_quoted_expr(s):
    """Return string s in appropriate quotes, using raw string if possible.
    
    Effectively this turns string: cd \ao\ao\
    to: r"cd \ao\ao\_"[:-1]
    
    Note the use of raw string and padding at the end to allow trailing
    backslash.
    """
    
    tail = ''
    tailpadding = ''
    raw  = ''
    if "\\" in s:
        raw = 'r'
        if s.endswith('\\'):
            tail = '[:-1]'
            tailpadding = '_'
    if '"' not in s:
        quote = '"'
    elif "'" not in s:
        quote = "'"
    elif '"""' not in s and not s.endswith('"'):
        quote = '"""'
    elif "'''" not in s and not s.endswith("'"):
        quote = "'''"
    else:
        # Give up, backslash-escaped string will do
        return '"%s"' % esc_quotes(s)
    res = ''.join([raw, quote, s, tailpadding, quote, tail])
    return res

# This function is used by ipython in a lot of places to make system calls.
# We need it to be slightly different under win32, due to the vagaries of
# 'network shares'.  A win32 override is below.

def system_shell(cmd, verbose=False, debug=False, header=''):
    """ Execute a command in the system shell; always return None.

    Parameters
    ----------
    cmd : str
        The command to execute.
    verbose : bool
        If True, print the command to be executed.
    debug : bool
        Only print, do not actually execute.
    header : str
        Header to print to screen prior to the executed command. No extra
        newlines are added.

    Description
    -----------
    This returns None so it can be conveniently used in interactive loops
    without getting the return value (typically 0) printed many times.
    """

    if verbose or debug: 
        print header + cmd

    # Flush stdout so we don't mangle python's buffering.
    sys.stdout.flush()
    if not debug:
        os.system(cmd)

# Override shell() for win32 to deal with network shares.
if os.name in ('nt', 'dos'):

    system_shell_ori = system_shell

    def system_shell(cmd, verbose=False, debug=False, header=''):
        if os.getcwd().startswith(r"\\"):
            path = os.getcwd()
            # Change to c drive (cannot be on UNC-share when issuing os.system,
            # as cmd.exe cannot handle UNC addresses).
            os.chdir("c:")
            # Issue pushd to the UNC-share and then run the command.
            try:
                system_shell_ori('"pushd %s&&"'%path+cmd,verbose,debug,header)
            finally:
                os.chdir(path)
        else:
            system_shell_ori(cmd,verbose,debug,header)

    system_shell.__doc__ = system_shell_ori.__doc__

def getoutputerror(cmd, verbose=False, debug=False, header='', split=False):
    """ Executes a command and returns the output.

    Parameters
    ----------
    cmd : str
        The command to execute.
    verbose : bool
        If True, print the command to be executed.
    debug : bool
        Only print, do not actually execute.
    header : str
        Header to print to screen prior to the executed command. No extra
        newlines are added.
    split : bool
        If True, return the output as a list split on newlines.

    """

    if verbose or debug: 
        print header+cmd

    if not cmd:
        # Return empty lists or strings.
        if split:
            return [], []
        else:
            return '', ''

    if not debug:
        # fixme: use subprocess.
        pin,pout,perr = os.popen3(cmd)
        tout = pout.read().rstrip()
        terr = perr.read().rstrip()
        pin.close()
        pout.close()
        perr.close()
        if split:
            return tout.split('\n'), terr.split('\n')
        else:
            return tout, terr

