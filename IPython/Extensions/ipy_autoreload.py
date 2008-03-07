"""
IPython extension: autoreload modules before executing the next line

Try:: 

    %autoreload?

for documentation.
"""

# Pauli Virtanen <pav@iki.fi>, 2008.
# Thomas Heller, 2000.
#
# This IPython module is written by Pauli Virtanen, based on the autoreload
# code by Thomas Heller.

#------------------------------------------------------------------------------
# Autoreload functionality
#------------------------------------------------------------------------------

import time, os, threading, sys, types, imp, inspect, traceback, atexit

def _get_compiled_ext():
    """Official way to get the extension of compiled files (.pyc or .pyo)"""
    for ext, mode, typ in imp.get_suffixes():
        if typ == imp.PY_COMPILED:
            return ext

PY_COMPILED_EXT = _get_compiled_ext()

class ModuleReloader(object):
    skipped = {}
    """Modules that failed to reload: {module: mtime-on-failed-reload, ...}"""
    
    modules = {}
    """Modules specially marked as autoreloadable."""

    skip_modules = {}
    """Modules specially marked as not autoreloadable."""

    check_all = True
    """Autoreload all modules, not just those listed in 'modules'"""
    
    def check(self, check_all=False):
        """Check whether some modules need to be reloaded."""
        
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
            dirname = os.path.dirname(filename)
            path, ext = os.path.splitext(filename)
            
            if ext.lower() == '.py':
                ext = PY_COMPILED_EXT
                filename = os.path.join(dirname, path + PY_COMPILED_EXT)
            
            if ext != PY_COMPILED_EXT:
                continue
            
            try:
                pymtime = os.stat(filename[:-1]).st_mtime
                if pymtime <= os.stat(filename).st_mtime:
                    continue
                if self.skipped.get(filename[:-1], None) == pymtime:
                    continue
            except OSError:
                continue
            
            try:
                superreload(m)
                if filename[:-1] in self.skipped:
                    del self.skipped[filename[:-1]]
            except:
                self.skipped[filename[:-1]] = pymtime

def update_function(old, new, attrnames):
    for name in attrnames:
        setattr(old, name, getattr(new, name))

def superreload(module, reload=reload):
    """Enhanced version of the builtin reload function.
    
    superreload replaces the class dictionary of every top-level
    class in the module with the new one automatically,
    as well as every function's code object.
    
    """

    module = reload(module)
    
    # iterate over all objects and update them
    count = 0
    for name, new_obj in module.__dict__.items():
        key = (module.__name__, name)
        if _old_objects.has_key(key):
            for old_obj in _old_objects[key]:
                if type(new_obj) == types.ClassType:
                    old_obj.__dict__.update(new_obj.__dict__)
                    count += 1
                elif type(new_obj) == types.FunctionType:
                    update_function(old_obj,
                           new_obj,
                           "func_code func_defaults func_doc".split())
                    count += 1
                elif type(new_obj) == types.MethodType:
                    update_function(old_obj.im_func,
                           new_obj.im_func,
                           "func_code func_defaults func_doc".split())
                    count += 1
    
    return module

reloader = ModuleReloader()

#------------------------------------------------------------------------------
# IPython monkey-patching
#------------------------------------------------------------------------------

import IPython.iplib

autoreload_enabled = False

def runcode_hook(self):
    if not autoreload_enabled:
        raise IPython.ipapi.TryNext
    try:
        reloader.check()
    except:
        pass


def enable_autoreload():
    global autoreload_enabled
    autoreload_enabled = True
    

def disable_autoreload():
    global autoreload_enabled
    autoreload_enabled = False
    
#------------------------------------------------------------------------------
# IPython connectivity
#------------------------------------------------------------------------------

import IPython.ipapi
ip = IPython.ipapi.get()

def autoreload_f(self, parameter_s=''):
    r""" %autoreload => Reload modules automatically

    %autoreload
    Reload all modules (except thoses excluded by %aimport) automatically now.

    %autoreload 1
    Reload all modules imported with %aimport every time before executing
    the Python code typed.

    %autoreload 2
    Reload all modules (except thoses excluded by %aimport) every time
    before executing the Python code typed.

    Reloading Python modules in a reliable way is in general
    difficult, and unexpected things may occur. Some of the common
    caveats relevant for 'autoreload' are:

    - Modules are not reloaded in any specific order, and no dependency
      analysis is done. For example, modules with 'from xxx import foo'
      retain old versions of 'foo' when 'xxx' is autoreloaded.
    - Functions or objects imported from the autoreloaded module to
      the interactive namespace are not updated.
    - C extension modules cannot be reloaded, and so cannot be
      autoreloaded.
    """
    if parameter_s == '':
        reloader.check(True)
    elif parameter_s == '0':
        disable_autoreload()
    elif parameter_s == '1':
        reloader.check_all = False
        enable_autoreload()
    elif parameter_s == '2':
        reloader.check_all = True
        enable_autoreload()

def aimport_f(self, parameter_s=''):
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
        to_reload = reloader.modules.keys()
        to_reload.sort()
        to_skip = reloader.skip_modules.keys()
        to_skip.sort()
        if reloader.check_all:
            print "Modules to reload:\nall-expect-skipped"
        else:
            print "Modules to reload:\n%s" % ' '.join(to_reload)
        print "\nModules to skip:\n%s" % ' '.join(to_skip)
    elif modname.startswith('-'):
        modname = modname[1:]
        try: del reloader.modules[modname]
        except KeyError: pass
        reloader.skip_modules[modname] = True
    else:
        try: del reloader.skip_modules[modname]
        except KeyError: pass
        reloader.modules[modname] = True

        mod = __import__(modname)
        ip.to_user_ns({modname: mod})

def init():
    ip.expose_magic('autoreload', autoreload_f)
    ip.expose_magic('aimport', aimport_f)
    ip.set_hook('pre_runcode_hook', runcode_hook)
    
init()