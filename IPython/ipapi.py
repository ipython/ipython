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
 
def _init_with_shell(ip):
    global magic
    magic = ip.ipmagic
    global system
    system = ip.ipsystem
    global set_hook
    set_hook = ip.set_hook
    
    global __IP
    __IP = ip

def options():
    """ All configurable variables """
    return __IP.rc

def user_ns():
    return __IP.user_ns

def expose_magic(magicname, func):
    ''' Expose own function as magic function for ipython 

    def foo_impl(self,parameter_s=''):
        """My very own magic!. (Use docstrings, IPython reads them)."""
        print 'Magic function. Passed parameter is between < >: <'+parameter_s+'>'
        print 'The self object is:',self

    ipapi.expose_magic("foo",foo_impl)
    '''
    
    from IPython import Magic
    import new
    im = new.instancemethod(func,__IP, __IP.__class__)
    setattr(__IP, "magic_" + magicname, im)

class asmagic:
    """ Decorator for exposing magics in a friendly 2.4 decorator form 
    
    @ip.asmagic("foo")
    def f(self,arg):
        pring "arg given:",arg
    
    After this, %foo is a magic function.
    """
    
    def __init__(self,magicname):
        self.name = magicname
        
    def __call__(self,f):
        expose_magic(self.name, f)
        return f

class ashook:
    """ Decorator for exposing magics in a friendly 2.4 decorator form 
    
    @ip.ashook("editor")
    def jed_editor(self,filename, linenum=None):
        import os
        if linenum is None: linenum = 0
        os.system('jed +%d %s' % (linenum, filename))
    
    """
    
    def __init__(self,name,priority=50):
        self.name = name
        self.prio = priority
        
    def __call__(self,f):
        set_hook(self.name, f, self.prio)
        return f


def ex(cmd):
    """ Execute a normal python statement """
    exec cmd in user_ns()