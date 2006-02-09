''' IPython customization API

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
import IPython.ipapi as ip

def ankka_f(self, arg):
    print "Ankka",self,"says uppercase:",arg.upper()

ip.expose_magic("ankka",ankka_f)

ip.magic('alias sayhi echo "Testing, hi ok"')
ip.magic('alias helloworld echo "Hello world"')
ip.system('pwd')

ip.ex('import re')
ip.ex("""
def funcci(a,b):
    print a+b
print funcci(3,4)
""")
ip.ex("funcci(348,9)")

def jed_editor(self,filename, linenum=None):
    print "Calling my own editor, jed ... via hook!"
    import os
    if linenum is None: linenum = 0
    os.system('jed +%d %s' % (linenum, filename))
    print "exiting jed"

ip.set_hook('editor',jed_editor)

o = ip.options()
o.autocall = 2  # FULL autocall mode

print "done!"
    
'''
 
 
class TryNext(Exception):
    """ Try next hook exception.
     
     Raise this in your hook function to indicate that the next
     hook handler should be used to handle the operation.
    """
 
   
# contains the most recently instantiated IPApi
_recent = None

def get():
    """ Get an IPApi object, or None if not running under ipython

    Running this should be the first thing you do when writing
    extensions that can be imported as normal modules. You can then 
    direct all the configuration operations against the returned 
    object.

    """

    return _recent

 
 
class IPApi:
    """ The actual API class for configuring IPython 
    
    You should do all of the IPython configuration by getting 
    an IPApi object with IPython.ipapi.get() and using the provided
    methods.
    
    """
    def __init__(self,ip):
        
        self.magic = ip.ipmagic
        
        self.system = ip.ipsystem
        
        self.set_hook = ip.set_hook
        
        self.set_custom_exc = ip.set_custom_exc
        
        self.IP = ip
        global _recent
        _recent = self

        
    
    def options(self):
        """ All configurable variables """
        return self.IP.rc
    
    def user_ns(self):
        return self.IP.user_ns
    
    def expose_magic(self,magicname, func):
        ''' Expose own function as magic function for ipython 
    
        def foo_impl(self,parameter_s=''):
            """My very own magic!. (Use docstrings, IPython reads them)."""
            print 'Magic function. Passed parameter is between < >: <'+parameter_s+'>'
            print 'The self object is:',self
    
        ipapi.expose_magic("foo",foo_impl)
        '''
                
        import new
        im = new.instancemethod(func,self.IP, self.IP.__class__)
        setattr(self.IP, "magic_" + magicname, im)
    
    
    def ex(self,cmd):
        """ Execute a normal python statement in user namespace """
        exec cmd in self.user_ns()
    
    def ev(self,expr):
        """ Evaluate python expression expr in user namespace 
        
        Returns the result of evaluation"""
        return eval(expr,self.user_ns())
    
    def meta(self):
        """ Get a session-specific data store
        
        Object returned by this method can be used to store
        data that should persist through the ipython session.
        """
        return self.IP.meta
    
    def getdb(self):
        """ Return a handle to persistent dict-like database
        
        Return a PickleShareDB object.
        """
        return self.IP.db
    def runlines(self,lines):
        """ Run the specified lines in interpreter, honoring ipython directives.
        
        This allows %magic and !shell escape notations.
        
        Takes either all lines in one string or list of lines.
        """
        if isinstance(lines,basestring):
            self.IP.runlines(lines)
        else:
            self.IP.runlines('\n'.join(lines))


def launch_new_instance(user_ns = None):
    """ Create and start a new ipython instance.
    
    This can be called even without having an already initialized 
    ipython session running.
    
    This is also used as the egg entry point for the 'ipython' script.
    
    """
    ses = create_session(user_ns)
    ses.mainloop()


def create_session(user_ns = None):    
    """ Creates, but does not launch an IPython session.
    
    Later on you can call obj.mainloop() on the returned object.
    
    This should *not* be run when a session exists already.
    
    """
    if user_ns is not None: 
        user_ns["__name__"] = user_ns.get("__name__",'ipy_session')
    import IPython
    return IPython.Shell.start(user_ns = user_ns)