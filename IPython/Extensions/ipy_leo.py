import IPython.ipapi
ip = IPython.ipapi.get()

from IPython.external.simplegeneric import generic 

@generic
def format_for_leo(obj):
    """ Convert obj to string representiation (for editing in Leo)"""
    return str(obj)

@format_for_leo.when_type(list)
def format_list(obj):
    return "\n".join(str(s) for s in obj)


def add_var(self,varname):
    ip = self.getapi()
    leo = ip.user_ns['leox']
    c,g = leo.c, leo.g
    nodename = '@ipy-var ' + varname
    p2 = g.findNodeAnywhere(c,nodename)
    if not c.positionExists(p2):
        p2 = c.currentPosition().insertAfter()
        c.setHeadString(p2,'@ipy-var ' + varname)
        
    c.setCurrentPosition(p2)
    val = ip.user_ns[varname]
    formatted = format_for_leo(val)
    c.setBodyString(p2,formatted)

def leo_f(self,s):
    ip = self.getapi()
    s = s.strip()
    if s in ip.user_ns:
        add_var(self,s)

ip.expose_magic('leo',leo_f)


    
    
    
    
    

