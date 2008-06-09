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
import weakref

def _get_compiled_ext():
    """Official way to get the extension of compiled files (.pyc or .pyo)"""
    for ext, mode, typ in imp.get_suffixes():
        if typ == imp.PY_COMPILED:
            return ext

PY_COMPILED_EXT = _get_compiled_ext()

class ModuleReloader(object):
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
                if self.failed.get(filename[:-1], None) == pymtime:
                    continue
            except OSError:
                continue
            
            try:
                superreload(m, reload, self.old_objects)
                if filename[:-1] in self.failed:
                    del self.failed[filename[:-1]]
            except:
                print >> sys.stderr, "[autoreload of %s failed: %s]" % (
                        modname, traceback.format_exc(1))
                self.failed[filename[:-1]] = pymtime

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
        old_name = module.__name__
        module.__dict__.clear()
        module.__dict__['__name__'] = old_name
    except (TypeError, AttributeError, KeyError):
        pass
    module = reload(module)
    
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

reloader = ModuleReloader()

#------------------------------------------------------------------------------
# IPython connectivity
#------------------------------------------------------------------------------
import IPython.ipapi

ip = IPython.ipapi.get()

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

def autoreload_f(self, parameter_s=''):
    r""" %autoreload => Reload modules automatically
    
    %autoreload
    Reload all modules (except those excluded by %aimport) automatically now.
    
    %autoreload 1
    Reload all modules imported with %aimport every time before executing
    the Python code typed.
    
    %autoreload 2
    Reload all modules (except those excluded by %aimport) every time
    before executing the Python code typed.
    
    Reloading Python modules in a reliable way is in general difficult,
    and unexpected things may occur. %autoreload tries to work
    around common pitfalls by replacing code objects of functions
    previously in the module with new versions. This makes the following
    things to work:

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
