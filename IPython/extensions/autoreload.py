"""
``autoreload`` is an IPython extension that reloads modules
automatically before executing the line of code typed.

This makes for example the following workflow possible:

.. sourcecode:: ipython

   In [1]: %load_ext autoreload

   In [2]: %autoreload 2

   In [3]: from foo import some_function

   In [4]: some_function()
   Out[4]: 42

   In [5]: # open foo.py in an editor and change some_function to return 43

   In [6]: some_function()
   Out[6]: 43

The module was reloaded without reloading it explicitly, and the
object imported with ``from foo import ...`` was also updated.

Usage
=====

The following magic commands are provided:

``%autoreload``

    Reload all modules (except those excluded by ``%aimport``)
    automatically now.

``%autoreload 0``

    Disable automatic reloading.

``%autoreload 1``

    Reload all modules imported with ``%aimport`` every time before
    executing the Python code typed.

``%autoreload 2``

    Reload all modules (except those excluded by ``%aimport``) every
    time before executing the Python code typed.

``%aimport``

    List modules which are to be automatically imported or not to be imported.

``%aimport foo``

    Import module 'foo' and mark it to be autoreloaded for ``%autoreload 1``

``%aimport -foo``

    Mark module 'foo' to not be autoreloaded.

Caveats
=======

Reloading Python modules in a reliable way is in general difficult,
and unexpected things may occur. ``%autoreload`` tries to work around
common pitfalls by replacing function code objects and parts of
classes previously in the module with new versions. This makes the
following things to work:

- Functions and classes imported via 'from xxx import foo' are upgraded
  to new versions when 'xxx' is reloaded.

- Methods and properties of classes are upgraded on reload, so that
  calling 'c.foo()' on an object 'c' created before the reload causes
  the new code for 'foo' to be executed.

Some of the known remaining caveats are:

- Replacing code objects does not always succeed: changing a @property
  in a class to an ordinary method or a method to a member variable
  can cause problems (but in old objects only).

- Functions that are removed (eg. via monkey-patching) from a module
  before it is reloaded are not upgraded.

- C extension modules cannot be reloaded, and so cannot be
  autoreloaded.

"""

skip_doctest = True

# Pauli Virtanen <pav@iki.fi>, 2008.
# Thomas Heller, 2000.
#
# This IPython module is written by Pauli Virtanen, based on the autoreload
# code by Thomas Heller.

#------------------------------------------------------------------------------
# Autoreload functionality
#------------------------------------------------------------------------------

import time, os, threading, sys, types, imp, inspect, traceback, atexit
import weakref
try:
    reload
except NameError:
    from imp import reload

def _get_compiled_ext():
    """Official way to get the extension of compiled files (.pyc or .pyo)"""
    for ext, mode, typ in imp.get_suffixes():
        if typ == imp.PY_COMPILED:
            return ext

PY_COMPILED_EXT = _get_compiled_ext()

class ModuleReloader(object):
    enabled = False
    """Whether this reloader is enabled"""

    failed = {}
    """Modules that failed to reload: {module: mtime-on-failed-reload, ...}"""

    modules = {}
    """Modules specially marked as autoreloadable."""

    skip_modules = {}
    """Modules specially marked as not autoreloadable."""

    check_all = True
    """Autoreload all modules, not just those listed in 'modules'"""

    old_objects = {}
    """(module-name, name) -> weakref, for replacing old code objects"""

    def mark_module_skipped(self, module_name):
        """Skip reloading the named module in the future"""
        try:
            del self.modules[module_name]
        except KeyError:
            pass
        self.skip_modules[module_name] = True

    def mark_module_reloadable(self, module_name):
        """Reload the named module in the future (if it is imported)"""
        try:
            del self.skip_modules[module_name]
        except KeyError:
            pass
        self.modules[module_name] = True

    def aimport_module(self, module_name):
        """Import a module, and mark it reloadable

        Returns
        -------
        top_module : module
            The imported module if it is top-level, or the top-level
        top_name : module
            Name of top_module

        """
        self.mark_module_reloadable(module_name)

        __import__(module_name)
        top_name = module_name.split('.')[0]
        top_module = sys.modules[top_name]
        return top_module, top_name

    def check(self, check_all=False):
        """Check whether some modules need to be reloaded."""

        if not self.enabled and not check_all:
            return

        if check_all or self.check_all:
            modules = sys.modules.keys()
        else:
            modules = self.modules.keys()

        for modname in modules:
            m = sys.modules.get(modname, None)

            if modname in self.skip_modules:
                continue

            if not hasattr(m, '__file__'):
                continue

            if m.__name__ == '__main__':
                # we cannot reload(__main__)
                continue

            filename = m.__file__
            path, ext = os.path.splitext(filename)

            if ext.lower() == '.py':
                ext = PY_COMPILED_EXT
                pyc_filename = path + PY_COMPILED_EXT
                py_filename = filename
            else:
                pyc_filename = filename
                py_filename = filename[:-1]

            if ext != PY_COMPILED_EXT:
                continue

            try:
                pymtime = os.stat(py_filename).st_mtime
                if pymtime <= os.stat(pyc_filename).st_mtime:
                    continue
                if self.failed.get(py_filename, None) == pymtime:
                    continue
            except OSError:
                continue

            try:
                superreload(m, reload, self.old_objects)
                if py_filename in self.failed:
                    del self.failed[py_filename]
            except:
                print >> sys.stderr, "[autoreload of %s failed: %s]" % (
                        modname, traceback.format_exc(1))
                self.failed[py_filename] = pymtime

#------------------------------------------------------------------------------
# superreload
#------------------------------------------------------------------------------

def update_function(old, new):
    """Upgrade the code object of a function"""
    for name in ['func_code', 'func_defaults', 'func_doc',
                 'func_closure', 'func_globals', 'func_dict']:
        try:
            setattr(old, name, getattr(new, name))
        except (AttributeError, TypeError):
            pass

def update_class(old, new):
    """Replace stuff in the __dict__ of a class, and upgrade
    method code objects"""
    for key in old.__dict__.keys():
        old_obj = getattr(old, key)

        try:
            new_obj = getattr(new, key)
        except AttributeError:
            # obsolete attribute: remove it
            try:
                delattr(old, key)
            except (AttributeError, TypeError):
                pass
            continue

        if update_generic(old_obj, new_obj): continue

        try:
            setattr(old, key, getattr(new, key))
        except (AttributeError, TypeError):
            pass # skip non-writable attributes

def update_property(old, new):
    """Replace get/set/del functions of a property"""
    update_generic(old.fdel, new.fdel)
    update_generic(old.fget, new.fget)
    update_generic(old.fset, new.fset)

def isinstance2(a, b, typ):
    return isinstance(a, typ) and isinstance(b, typ)

UPDATE_RULES = [
    (lambda a, b: isinstance2(a, b, types.ClassType),
     update_class),
    (lambda a, b: isinstance2(a, b, types.TypeType),
     update_class),
    (lambda a, b: isinstance2(a, b, types.FunctionType),
     update_function),
    (lambda a, b: isinstance2(a, b, property),
     update_property),
    (lambda a, b: isinstance2(a, b, types.MethodType),
     lambda a, b: update_function(a.im_func, b.im_func)),
]

def update_generic(a, b):
    for type_check, update in UPDATE_RULES:
        if type_check(a, b):
            update(a, b)
            return True
    return False

class StrongRef(object):
    def __init__(self, obj):
        self.obj = obj
    def __call__(self):
        return self.obj

def superreload(module, reload=reload, old_objects={}):
    """Enhanced version of the builtin reload function.

    superreload remembers objects previously in the module, and

    - upgrades the class dictionary of every old class in the module
    - upgrades the code object of every old function and method
    - clears the module's namespace before reloading

    """

    # collect old objects in the module
    for name, obj in module.__dict__.items():
        if not hasattr(obj, '__module__') or obj.__module__ != module.__name__:
            continue
        key = (module.__name__, name)
        try:
            old_objects.setdefault(key, []).append(weakref.ref(obj))
        except TypeError:
            # weakref doesn't work for all types;
            # create strong references for 'important' cases
            if isinstance(obj, types.ClassType):
                old_objects.setdefault(key, []).append(StrongRef(obj))

    # reload module
    try:
        # clear namespace first from old cruft
        old_dict = module.__dict__.copy()
        old_name = module.__name__
        module.__dict__.clear()
        module.__dict__['__name__'] = old_name
    except (TypeError, AttributeError, KeyError):
        pass

    try:
        module = reload(module)
    except:
        # restore module dictionary on failed reload
        module.__dict__.update(old_dict)
        raise

    # iterate over all objects and update functions & classes
    for name, new_obj in module.__dict__.items():
        key = (module.__name__, name)
        if key not in old_objects: continue

        new_refs = []
        for old_ref in old_objects[key]:
            old_obj = old_ref()
            if old_obj is None: continue
            new_refs.append(old_ref)
            update_generic(old_obj, new_obj)

        if new_refs:
            old_objects[key] = new_refs
        else:
            del old_objects[key]

    return module

#------------------------------------------------------------------------------
# IPython connectivity
#------------------------------------------------------------------------------

from IPython.core.plugin import Plugin
from IPython.core.hooks import TryNext

class AutoreloadInterface(object):
    def __init__(self, *a, **kw):
        super(AutoreloadInterface, self).__init__(*a, **kw)
        self._reloader = ModuleReloader()
        self._reloader.check_all = False

    def magic_autoreload(self, ipself, parameter_s=''):
        r"""%autoreload => Reload modules automatically

        %autoreload
        Reload all modules (except those excluded by %aimport) automatically
        now.

        %autoreload 0
        Disable automatic reloading.

        %autoreload 1
        Reload all modules imported with %aimport every time before executing
        the Python code typed.

        %autoreload 2
        Reload all modules (except those excluded by %aimport) every time
        before executing the Python code typed.

        Reloading Python modules in a reliable way is in general
        difficult, and unexpected things may occur. %autoreload tries to
        work around common pitfalls by replacing function code objects and
        parts of classes previously in the module with new versions. This
        makes the following things to work:

        - Functions and classes imported via 'from xxx import foo' are upgraded
          to new versions when 'xxx' is reloaded.

        - Methods and properties of classes are upgraded on reload, so that
          calling 'c.foo()' on an object 'c' created before the reload causes
          the new code for 'foo' to be executed.

        Some of the known remaining caveats are:

        - Replacing code objects does not always succeed: changing a @property
          in a class to an ordinary method or a method to a member variable
          can cause problems (but in old objects only).

        - Functions that are removed (eg. via monkey-patching) from a module
          before it is reloaded are not upgraded.

        - C extension modules cannot be reloaded, and so cannot be
          autoreloaded.

        """
        if parameter_s == '':
            self._reloader.check(True)
        elif parameter_s == '0':
            self._reloader.enabled = False
        elif parameter_s == '1':
            self._reloader.check_all = False
            self._reloader.enabled = True
        elif parameter_s == '2':
            self._reloader.check_all = True
            self._reloader.enabled = True

    def magic_aimport(self, ipself, parameter_s='', stream=None):
        """%aimport => Import modules for automatic reloading.

        %aimport
        List modules to automatically import and not to import.

        %aimport foo
        Import module 'foo' and mark it to be autoreloaded for %autoreload 1

        %aimport -foo
        Mark module 'foo' to not be autoreloaded for %autoreload 1

        """

        modname = parameter_s
        if not modname:
            to_reload = self._reloader.modules.keys()
            to_reload.sort()
            to_skip = self._reloader.skip_modules.keys()
            to_skip.sort()
            if stream is None:
                stream = sys.stdout
            if self._reloader.check_all:
                stream.write("Modules to reload:\nall-except-skipped\n")
            else:
                stream.write("Modules to reload:\n%s\n" % ' '.join(to_reload))
            stream.write("\nModules to skip:\n%s\n" % ' '.join(to_skip))
        elif modname.startswith('-'):
            modname = modname[1:]
            self._reloader.mark_module_skipped(modname)
        else:
            top_module, top_name = self._reloader.aimport_module(modname)

            # Inject module to user namespace
            ipself.push({top_name: top_module})

    def pre_run_code_hook(self, ipself):
        if not self._reloader.enabled:
            raise TryNext
        try:
            self._reloader.check()
        except:
            pass

class AutoreloadPlugin(AutoreloadInterface, Plugin):
    def __init__(self, shell=None, config=None):
        super(AutoreloadPlugin, self).__init__(shell=shell, config=config)

        self.shell.define_magic('autoreload', self.magic_autoreload)
        self.shell.define_magic('aimport', self.magic_aimport)
        self.shell.set_hook('pre_run_code_hook', self.pre_run_code_hook)

_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        plugin = AutoreloadPlugin(shell=ip, config=ip.config)
        ip.plugin_manager.register_plugin('autoreload', plugin)
        _loaded = True
