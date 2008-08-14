"""IPython customization API

Your one-stop module for configuring & extending ipython

The API will probably break when ipython 1.0 is released, but so 
will the other configuration method (rc files).

All names prefixed by underscores are for internal use, not part 
of the public api.

Below is an example that you can just put to a module and import from ipython. 

A good practice is to install the config script below as e.g. 

~/.ipython/my_private_conf.py

And do 

import_mod my_private_conf 

in ~/.ipython/ipythonrc

That way the module is imported at startup and you can have all your
personal configuration (as opposed to boilerplate ipythonrc-PROFILENAME 
stuff) in there. 

-----------------------------------------------
import IPython.ipapi
ip = IPython.ipapi.get()

def ankka_f(self, arg):
    print 'Ankka',self,'says uppercase:',arg.upper()

ip.expose_magic('ankka',ankka_f)

ip.magic('alias sayhi echo "Testing, hi ok"')
ip.magic('alias helloworld echo "Hello world"')
ip.system('pwd')

ip.ex('import re')
ip.ex('''
def funcci(a,b):
    print a+b
print funcci(3,4)
''')
ip.ex('funcci(348,9)')

def jed_editor(self,filename, linenum=None):
    print 'Calling my own editor, jed ... via hook!'
    import os
    if linenum is None: linenum = 0
    os.system('jed +%d %s' % (linenum, filename))
    print 'exiting jed'

ip.set_hook('editor',jed_editor)

o = ip.options
o.autocall = 2  # FULL autocall mode

print 'done!'
"""

#-----------------------------------------------------------------------------
# Modules and globals

# stdlib imports
import __builtin__
import sys

# contains the most recently instantiated IPApi
_RECENT_IP = None

#-----------------------------------------------------------------------------
# Code begins

class TryNext(Exception):
    """Try next hook exception.
     
    Raise this in your hook function to indicate that the next hook handler
    should be used to handle the operation.  If you pass arguments to the
    constructor those arguments will be used by the next hook instead of the
    original ones.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class UsageError(Exception):
    """ Error in magic function arguments, etc.
    
    Something that probably won't warrant a full traceback, but should
    nevertheless interrupt a macro / batch file.   
    """


class IPyAutocall:
    """ Instances of this class are always autocalled
    
    This happens regardless of 'autocall' variable state. Use this to
    develop macro-like mechanisms.
    """
    
    def set_ip(self,ip):
        """ Will be used to set _ip point to current ipython instance b/f call
        
        Override this method if you don't want this to happen.
        
        """
        self._ip = ip
    

class IPythonNotRunning:
    """Dummy do-nothing class.

    Instances of this class return a dummy attribute on all accesses, which
    can be called and warns.  This makes it easier to write scripts which use
    the ipapi.get() object for informational purposes to operate both with and
    without ipython.  Obviously code which uses the ipython object for
    computations will not work, but this allows a wider range of code to
    transparently work whether ipython is being used or not."""

    def __init__(self,warn=True):
        if warn:
            self.dummy = self._dummy_warn
        else:
            self.dummy = self._dummy_silent
    
    def __str__(self):
        return "<IPythonNotRunning>"

    __repr__ = __str__

    def __getattr__(self,name):
        return self.dummy

    def _dummy_warn(self,*args,**kw):
        """Dummy function, which doesn't do anything but warn."""

        print ("IPython is not running, this is a dummy no-op function")

    def _dummy_silent(self,*args,**kw):
        """Dummy function, which doesn't do anything and emits no warnings."""
        pass


def get(allow_dummy=False,dummy_warn=True):
    """Get an IPApi object.

    If allow_dummy is true, returns an instance of IPythonNotRunning 
    instead of None if not running under IPython.

    If dummy_warn is false, the dummy instance will be completely silent.

    Running this should be the first thing you do when writing extensions that
    can be imported as normal modules. You can then direct all the
    configuration operations against the returned object.
    """
    global _RECENT_IP
    if allow_dummy and not _RECENT_IP:
        _RECENT_IP = IPythonNotRunning(dummy_warn)
    return _RECENT_IP


class IPApi(object):
    """ The actual API class for configuring IPython 
    
    You should do all of the IPython configuration by getting an IPApi object
    with IPython.ipapi.get() and using the attributes and methods of the
    returned object."""
    
    def __init__(self,ip):
        
        global _RECENT_IP

        # All attributes exposed here are considered to be the public API of
        # IPython.  As needs dictate, some of these may be wrapped as
        # properties.

        self.magic = ip.ipmagic
        
        self.system = ip.system
        
        self.set_hook = ip.set_hook
        
        self.set_custom_exc = ip.set_custom_exc

        self.user_ns = ip.user_ns
        self.user_ns['_ip'] = self

        self.set_crash_handler = ip.set_crash_handler

        # Session-specific data store, which can be used to store
        # data that should persist through the ipython session.
        self.meta =  ip.meta
    
        # The ipython instance provided
        self.IP = ip

        self.extensions = {}

        self.dbg = DebugTools(self)
        
        _RECENT_IP = self

    # Use a property for some things which are added to the instance very
    # late.  I don't have time right now to disentangle the initialization
    # order issues, so a property lets us delay item extraction while
    # providing a normal attribute API.
    def get_db(self):
        """A handle to persistent dict-like database (a PickleShareDB object)"""
        return self.IP.db

    db = property(get_db,None,None,get_db.__doc__)

    def get_options(self):
        """All configurable variables."""
        
        # catch typos by disabling new attribute creation. If new attr creation
        # is in fact wanted (e.g. when exposing new options), do
        # allow_new_attr(True) for the received rc struct.
        
        self.IP.rc.allow_new_attr(False)
        return self.IP.rc

    options = property(get_options,None,None,get_options.__doc__)
    
    def expose_magic(self,magicname, func):
        """Expose own function as magic function for ipython 
    
        def foo_impl(self,parameter_s=''):
            'My very own magic!. (Use docstrings, IPython reads them).'
            print 'Magic function. Passed parameter is between < >:'
            print '<%s>' % parameter_s
            print 'The self object is:',self
    
        ipapi.expose_magic('foo',foo_impl)
        """
        
        import new
        im = new.instancemethod(func,self.IP, self.IP.__class__)
        old = getattr(self.IP, "magic_" + magicname, None)
        if old:
            self.dbg.debug_stack("Magic redefinition '%s', old %s" %
                                 (magicname,old) )
            
        setattr(self.IP, "magic_" + magicname, im)
    
    def ex(self,cmd):
        """ Execute a normal python statement in user namespace """
        exec cmd in self.user_ns
    
    def ev(self,expr):
        """ Evaluate python expression expr in user namespace 
        
        Returns the result of evaluation"""
        return eval(expr,self.user_ns)
    
    def runlines(self,lines):
        """ Run the specified lines in interpreter, honoring ipython directives.
        
        This allows %magic and !shell escape notations.
        
        Takes either all lines in one string or list of lines.
        """

        def cleanup_ipy_script(script):
            """ Make a script safe for _ip.runlines() 
            
            - Removes empty lines Suffixes all indented blocks that end with
            - unindented lines with empty lines
            """
            
            res = []
            lines = script.splitlines()

            level = 0
            for l in lines:
                lstripped = l.lstrip()
                stripped = l.strip()                
                if not stripped:
                    continue
                newlevel = len(l) - len(lstripped)
                def is_secondary_block_start(s):
                    if not s.endswith(':'):
                        return False
                    if (s.startswith('elif') or 
                        s.startswith('else') or 
                        s.startswith('except') or
                        s.startswith('finally')):
                        return True
                        
                if level > 0 and newlevel == 0 and \
                       not is_secondary_block_start(stripped): 
                    # add empty line
                    res.append('')
                    
                res.append(l)
                level = newlevel
            return '\n'.join(res) + '\n'
        
        if isinstance(lines,basestring):
            script = lines            
        else:
            script = '\n'.join(lines)
        clean=cleanup_ipy_script(script)
        # print "_ip.runlines() script:\n",clean # dbg
        self.IP.runlines(clean)
        
    def to_user_ns(self,vars, interactive = True):
        """Inject a group of variables into the IPython user namespace.

        Inputs:

         - vars: string with variable names separated by whitespace, or a
         dict with name/value pairs.

         - interactive: if True (default), the var will be listed with
        %whos et. al.
         
        This utility routine is meant to ease interactive debugging work,
        where you want to easily propagate some internal variable in your code
        up to the interactive namespace for further exploration.

        When you run code via %run, globals in your script become visible at
        the interactive prompt, but this doesn't happen for locals inside your
        own functions and methods.  Yet when debugging, it is common to want
        to explore some internal variables further at the interactive propmt.

        Examples:

        To use this, you first must obtain a handle on the ipython object as
        indicated above, via:

        import IPython.ipapi
        ip = IPython.ipapi.get()

        Once this is done, inside a routine foo() where you want to expose
        variables x and y, you do the following:

        def foo():
            ...
            x = your_computation()
            y = something_else()
            
            # This pushes x and y to the interactive prompt immediately, even
            # if this routine crashes on the next line after:
            ip.to_user_ns('x y')
            ...
            
            # To expose *ALL* the local variables from the function, use:
            ip.to_user_ns(locals())

            ...
            # return           
        

        If you need to rename variables, the dict input makes it easy.  For
        example, this call exposes variables 'foo' as 'x' and 'bar' as 'y'
        in IPython user namespace:

        ip.to_user_ns(dict(x=foo,y=bar))    
        """

        # print 'vars given:',vars # dbg
        
        # We need a dict of name/value pairs to do namespace updates.
        if isinstance(vars,dict):
            # If a dict was given, no need to change anything.
            vdict = vars
        elif isinstance(vars,basestring):
            # If a string with names was given, get the caller's frame to
            # evaluate the given names in
            cf = sys._getframe(1)
            vdict = {}
            for name in vars.split():
                try:
                    vdict[name] = eval(name,cf.f_globals,cf.f_locals)
                except:
                    print ('could not get var. %s from %s' %
                    (name,cf.f_code.co_name))
        else:
            raise ValueError('vars must be a string or a dict')
            
        # Propagate variables to user namespace
        self.user_ns.update(vdict)

        # And configure interactive visibility
        config_ns = self.IP.user_config_ns
        if interactive:
            for name,val in vdict.iteritems():
                config_ns.pop(name,None)
        else:
            for name,val in vdict.iteritems():
                config_ns[name] = val                    

    def expand_alias(self,line):
        """ Expand an alias in the command line 
        
        Returns the provided command line, possibly with the first word 
        (command) translated according to alias expansion rules.
        
        [ipython]|16> _ip.expand_aliases("np myfile.txt")
                 <16> 'q:/opt/np/notepad++.exe myfile.txt'
        """
        
        pre,fn,rest = self.IP.split_user_input(line)
        res = pre + self.IP.expand_aliases(fn,rest)
        return res

    def itpl(self, s, depth = 1):
        """ Expand Itpl format string s.
        
        Only callable from command line (i.e. prefilter results);
        If you use in your scripts, you need to use a bigger depth!
        """
        return self.IP.var_expand(s, depth)
        
    def defalias(self, name, cmd):
        """ Define a new alias
        
        _ip.defalias('bb','bldmake bldfiles')
        
        Creates a new alias named 'bb' in ipython user namespace
        """

        self.dbg.check_hotname(name)
        
        if name in self.IP.alias_table:
            self.dbg.debug_stack("Alias redefinition: '%s' => '%s' (old '%s')"
                                 % (name, cmd, self.IP.alias_table[name]))

        if callable(cmd):
            self.IP.alias_table[name] = cmd
            import IPython.shadowns
            setattr(IPython.shadowns, name,cmd)
            return
            
        if isinstance(cmd,basestring):
            nargs = cmd.count('%s')
            if nargs>0 and cmd.find('%l')>=0:
                raise Exception('The %s and %l specifiers are mutually '
                                'exclusive in alias definitions.')
                  
            self.IP.alias_table[name] = (nargs,cmd)
            return
        
        # just put it in - it's probably (0,'foo')
        self.IP.alias_table[name] = cmd
    
    def defmacro(self, *args):
        """ Define a new macro
    
        2 forms of calling:
        
        mac = _ip.defmacro('print "hello"\nprint "world"')
        
        (doesn't put the created macro on user namespace)
        
        _ip.defmacro('build', 'bldmake bldfiles\nabld build winscw udeb')
        
        (creates a macro named 'build' in user namespace)
        """
        
        import IPython.macro
        
        if len(args) == 1:
            return IPython.macro.Macro(args[0])
        elif len(args) == 2:
            self.user_ns[args[0]] = IPython.macro.Macro(args[1])
        else:
            return Exception("_ip.defmacro must be called with 1 or 2 arguments")
        
    def set_next_input(self, s):
        """ Sets the 'default' input string for the next command line.
        
        Requires readline.
        
        Example:
        
        [D:\ipython]|1> _ip.set_next_input("Hello Word")
        [D:\ipython]|2> Hello Word_  # cursor is here        
        """

        self.IP.rl_next_input = s

    def load(self, mod):
        """ Load an extension.
        
        Some modules should (or must) be 'load()':ed, rather than just imported.
        
        Loading will do:
        
        - run init_ipython(ip)
        - run ipython_firstrun(ip)
        """
        
        if mod in self.extensions:
            # just to make sure we don't init it twice
            # note that if you 'load' a module that has already been
            # imported, init_ipython gets run anyway
            
            return self.extensions[mod]
        __import__(mod)
        m = sys.modules[mod]
        if hasattr(m,'init_ipython'):
            m.init_ipython(self)
            
        if hasattr(m,'ipython_firstrun'):
            already_loaded = self.db.get('firstrun_done', set())
            if mod not in already_loaded:
                m.ipython_firstrun(self)
                already_loaded.add(mod)
                self.db['firstrun_done'] = already_loaded
            
        self.extensions[mod] = m
        return m


class DebugTools:
    """ Used for debugging mishaps in api usage
    
    So far, tracing redefinitions is supported.
    """
    
    def __init__(self, ip):
        self.ip = ip
        self.debugmode = False
        self.hotnames = set()
        
    def hotname(self, name_to_catch):
        self.hotnames.add(name_to_catch)
        
    def debug_stack(self, msg = None):
        if not self.debugmode:
            return
        
        import traceback
        if msg is not None:
            print '====== %s  ========' % msg
        traceback.print_stack()

    def check_hotname(self,name):
        if name in self.hotnames:
            self.debug_stack( "HotName '%s' caught" % name)


def launch_new_instance(user_ns = None,shellclass = None):
    """ Make and start a new ipython instance.
    
    This can be called even without having an already initialized 
    ipython session running.
    
    This is also used as the egg entry point for the 'ipython' script.
    
    """
    ses = make_session(user_ns,shellclass)
    ses.mainloop()


def make_user_ns(user_ns = None):
    """Return a valid user interactive namespace.

    This builds a dict with the minimal information needed to operate as a
    valid IPython user namespace, which you can pass to the various embedding
    classes in ipython.

    This API is currently deprecated. Use ipapi.make_user_namespaces() instead
    to make both the local and global namespace objects simultaneously.

    :Parameters:
        user_ns : dict-like, optional
            The current user namespace. The items in this namespace should be
            included in the output. If None, an appropriate blank namespace
            should be created.

    :Returns:
        A dictionary-like object to be used as the local namespace of the
        interpreter.
    """

    raise NotImplementedError


def make_user_global_ns(ns = None):
    """Return a valid user global namespace.

    Similar to make_user_ns(), but global namespaces are really only needed in
    embedded applications, where there is a distinction between the user's
    interactive namespace and the global one where ipython is running.

    This API is currently deprecated. Use ipapi.make_user_namespaces() instead
    to make both the local and global namespace objects simultaneously.

    :Parameters:
        ns : dict, optional
            The current user global namespace. The items in this namespace
            should be included in the output. If None, an appropriate blank
            namespace should be created.

    :Returns:
        A true dict to be used as the global namespace of the interpreter.
    """

    raise NotImplementedError

# Record the true objects in order to be able to test if the user has overridden
# these API functions.
_make_user_ns = make_user_ns
_make_user_global_ns = make_user_global_ns


def make_user_namespaces(user_ns = None,user_global_ns = None):
    """Return a valid local and global user interactive namespaces.

    This builds a dict with the minimal information needed to operate as a
    valid IPython user namespace, which you can pass to the various embedding
    classes in ipython.  The default implementation returns the same dict for
    both the locals and the globals to allow functions to refer to variables in
    the namespace.  Customized implementations can return different dicts.  The
    locals dictionary can actually be anything following the basic mapping
    protocol of a dict, but the globals dict must be a true dict, not even
    a subclass.  It is recommended that any custom object for the locals
    namespace synchronize with the globals dict somehow.

    Raises TypeError if the provided globals namespace is not a true dict.

    :Parameters:
        user_ns : dict-like, optional
            The current user namespace. The items in this namespace should be
            included in the output. If None, an appropriate blank namespace
            should be created.
        user_global_ns : dict, optional
            The current user global namespace. The items in this namespace
            should be included in the output. If None, an appropriate blank
            namespace should be created.

    :Returns:
        A tuple pair of dictionary-like object to be used as the local namespace
        of the interpreter and a dict to be used as the global namespace.
    """

    if user_ns is None:
        if make_user_ns is not _make_user_ns:
            # Old API overridden.
            # FIXME: Issue DeprecationWarning, or just let the old API live on?
            user_ns = make_user_ns(user_ns)
        else:
            # Set __name__ to __main__ to better match the behavior of the
            # normal interpreter.
            user_ns = {'__name__'     :'__main__',
                       '__builtins__' : __builtin__,
                       }
    else:
        user_ns.setdefault('__name__','__main__')
        user_ns.setdefault('__builtins__',__builtin__)

    if user_global_ns is None:
        if make_user_global_ns is not _make_user_global_ns:
            # Old API overridden.
            user_global_ns = make_user_global_ns(user_global_ns)
        else:
            user_global_ns = user_ns
    if type(user_global_ns) is not dict:
        raise TypeError("user_global_ns must be a true dict; got %r"
            % type(user_global_ns))

    return user_ns, user_global_ns


def make_session(user_ns = None, shellclass = None):
    """Makes, but does not launch an IPython session.
    
    Later on you can call obj.mainloop() on the returned object.

    Inputs:

      - user_ns(None): a dict to be used as the user's namespace with initial
      data.
    
    WARNING: This should *not* be run when a session exists already."""

    import IPython.Shell
    if shellclass is None:
        return IPython.Shell.start(user_ns)
    return shellclass(user_ns = user_ns)
