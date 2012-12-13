# -*- coding: utf-8 -*-
"""
Fortran f2py related magics.

Author:
* David Trémouilles

"""
#-----------------------------------------------------------------------------
# Copyright (C) 2010-2012, IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

from __future__ import print_function

import imp
import io
import os
import sys
import time

try:
    import hashlib
except ImportError:
    import md5 as hashlib

from numpy.f2py.f2py2e import run_compile


from IPython.core import magic_arguments
from IPython.core.magic import (Magics, magics_class, cell_magic)
from IPython.utils import py3compat
from IPython.core.displaypub import publish_display_data

import numpy.f2py as f2py


@magics_class
class F2pyMagics(Magics):
    """Magics for Fortran code cell using f2py"""
    def __init__(self, shell):
        Magics.__init__(self, shell)

        # Search the extension suffix for compiled modules.
        for elem in imp.get_suffixes():
            #elem = (ext, mode, typ)
            if elem[2] == imp.C_EXTENSION:
                self.so_ext = elem[0]
                break

    def _import_all(self, module):
        """Import everything from the code cell"""
        for key, value in module.__dict__.items():
            if not key.startswith('__'):
                self.shell.push({key: value})
                publish_display_data('F2pyMagic.Fortran',
                                {'text/plain': "%s is ready for use" % key})

    @magic_arguments.magic_arguments()
    @magic_arguments.argument(
        '-f', '--force', action='store_true', default=False,
        help="Force the compilation of a new module, even if the source "
             "has been previously compiled."
        )
    @cell_magic
    def f2py(self, line, cell):
        """Compile and import everything from a Fortran code cell.

        The contents of the cell are written to a `.f90` file in the
        directory `IPYTHONDIR/f2py` using a filename with the hash of the
        code. This file is then compiled. The resulting module
        is imported and all of its symbols are injected into the user's
        namespace::

        %%f2py
        subroutine dbl(x)
            real(8), intent(inout) :: x
            x = 2 * x
        end subroutine
        """
        args = magic_arguments.parse_argstring(self.f2py, line)
        code = cell if cell.endswith('\n') else cell + '\n'
        lib_dir = os.path.join(self.shell.ipython_dir, 'f2py')

        key = code, sys.version_info, sys.executable, f2py.__version__.version

        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        if args.force:
            # Force a new module name by adding the current time to the
            # key which is hashed to determine the module name.
            key += time.time(),

        module_name = ("_fortran_magic_" +
                       hashlib.md5(str(key).encode('utf-8')).hexdigest())
        module_path = os.path.join(lib_dir, module_name + self.so_ext)


        have_module = lambda: os.path.isfile(module_path)

        if not have_module():
            f90_file = os.path.join(lib_dir, module_name + '.f90')
            f2py_out = os.path.join(lib_dir, module_name + '.f2pyout')
            f90_file = py3compat.cast_bytes_py2(f90_file,
                                        encoding=sys.getfilesystemencoding())
            with io.open(f90_file, 'w', encoding='utf-8') as codefile:
                codefile.write(code)

            extra_args = ''
            args = '-c -c %s -m %s %s' % (extra_args, module_name, f90_file)
            # Execute f2py2e.run_compile in lib_dir
            # to get the module.so file there
            execute_in = os.path.abspath(lib_dir)
            oldcwd = os.path.abspath(os.getcwd())
            os.chdir(execute_in)
            try:
                # f2py require sys.stdout.fileno to be set
                getattr(sys.stdout, "fileno")
            except AttributeError:
                sys.stdout.fileno = lambda: None
            # Prepare sys.argv with the args for f2py
            saved_sys_argv = sys.argv
            sys.argv = args.split()
            saved_sys_stdout = sys.stdout
            output = open(f2py_out, 'w')
            sys.stdout = output
            try:
                run_compile()
            except:
                output.close()
                sys.stdout = saved_sys_stdout
                messages = open(f2py_out, 'r').read()
                publish_display_data('F2pyMagic.Fortran',
                        {'text/plain': "Something went wrong...\n" + messages})
            else:
                output.close()
                sys.stdout = saved_sys_stdout
                publish_display_data('F2pyMagic.Fortran',
                            {'text/plain': "Compilation went OK..."})

            sys.argv = saved_sys_argv
            os.chdir(oldcwd)


        if have_module():
            module = imp.load_dynamic(module_name, module_path)
            self._import_all(module)




def load_ipython_extension(ipy):
    """Load the extension in IPython."""
    ipy.register_magics(F2pyMagics)
