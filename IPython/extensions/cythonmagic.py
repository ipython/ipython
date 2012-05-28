# -*- coding: utf-8 -*-
"""
Cython related magics.

Author:
* Brian Granger

Parts of this code were taken from Cython.inline.
"""
#-----------------------------------------------------------------------------
# Copyright (C) 2010-2011, IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os, sys
from importlib import import_module
import imp

try:
    import hashlib
except ImportError:
    import md5 as hashlib

from distutils.core import Distribution, Extension
from distutils.command.build_ext import build_ext

from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.testing.skipdoctest import skip_doctest
from IPython.core.magic_arguments import (
    argument, magic_arguments, parse_argstring
)

import Cython
from Cython.Compiler.Errors import CompileError
from Cython.Compiler.Main import Context, default_options
from Cython.Build.Dependencies import cythonize


@magics_class
class CythonMagics(Magics):

    def __init__(self, shell):
        super(CythonMagics,self).__init__(shell)
        self._reloads = {}
        self._code_cache = {}

    def _import_all(self, module):
        for k,v in module.__dict__.items():
            if not k.startswith('__'):
                self.shell.push({k:v})

    @cell_magic
    def cython_inline(self, line, cell):
        """Compile and run a Cython code cell using Cython.inline."""
        locs = self.shell.user_global_ns
        globs = self.shell.user_ns
        return Cython.inline(cell, locals=locs, globals=globs)

    @cell_magic
    def cython_pyximport(self, line, cell):
        """Compile and import a Cython code cell using pyximport."""
        module_name = line.strip()
        if not module_name:
            raise ValueError('module name must be given')
        fname = module_name + '.pyx'
        with open(fname, 'w') as f:
            f.write(cell)
        if 'pyximport' not in sys.modules:
            import pyximport
            pyximport.install(reload_support=True)
        if module_name in self._reloads:
            module = self._reloads[module_name]
            reload(module)
        else:
            module = import_module(module_name)
            self._reloads[module_name] = module
        self._import_all(module)

    @magic_arguments()
    @argument(
        '-f', '--force', action='store_true', default=False,
        help="Force the compilation of the pyx module even if it hasn't changed"
    )
    @cell_magic
    def cython(self, line, cell):
        """Compile and import everything from a Cython code cell."""
        args = parse_argstring(self.cython, line)
        code = cell if cell.endswith('\n') else cell+'\n'
        lib_dir=os.path.expanduser('~/.cython/magic')
        cython_include_dirs=['.']
        force=args.force
        quiet=True
        ctx = Context(cython_include_dirs, default_options)
        key = code, sys.version_info, sys.executable, Cython.__version__
        module_name = "_cython_magic_" + hashlib.md5(str(key).encode('utf-8')).hexdigest()
        so_ext = [ ext for ext,_,mod_type in imp.get_suffixes() if mod_type == imp.C_EXTENSION ][0]
        module_path = os.path.join(lib_dir, module_name+so_ext)

        if not os.path.exists(lib_dir):
            os.makedirs(lib_dir)

        if force or not os.path.isfile(module_path):
            cflags = []
            c_include_dirs = []
            if 'numpy' in code:
                import numpy
                c_include_dirs.append(numpy.get_include())
            pyx_file = os.path.join(lib_dir, module_name + '.pyx')
            with open(pyx_file, 'w') as f:            
                f.write(code)
            extension = Extension(
                name = module_name,
                sources = [pyx_file],
                include_dirs = c_include_dirs,
                extra_compile_args = cflags
            )
            build_extension = build_ext(Distribution())
            build_extension.finalize_options()
            try:
                build_extension.extensions = cythonize([extension], ctx=ctx, quiet=quiet)
            except CompileError:
                return
            build_extension.build_temp = os.path.dirname(pyx_file)
            build_extension.build_lib  = lib_dir
            build_extension.run()
            self._code_cache[key] = module_name

        module = imp.load_dynamic(module_name, module_path)
        self._import_all(module)


_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(CythonMagics)
        _loaded = True
