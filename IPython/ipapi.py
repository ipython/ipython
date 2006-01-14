''' IPython customization API

Your one-stop module for configuring ipython

This is experimental, use at your own risk.

All names prefixed by underscores are for internal use, not part 
of the public api.

No formal doc yet, here's an example that you can just put 
to a module and import from ipython.

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
    
    setattr(Magic.Magic, "magic_" + magicname, func)
    
def ex(cmd):
    """ Execute a normal python statement """
    exec cmd in user_ns()