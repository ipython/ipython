""" Leo plugin for IPython

Example use:

nodes.foo = "hello world"

  -> create '@ipy foo' node with text "hello world"

Access works also, and so does tab completion.
   
"""
import IPython.ipapi
import IPython.genutils
import IPython.generics
import re



ip = IPython.ipapi.get()
leo = ip.user_ns['leox']
c,g = leo.c, leo.g

# will probably be overwritten by user, but handy for experimentation early on
ip.user_ns['c'] = c
ip.user_ns['g'] = g


from IPython.external.simplegeneric import generic 
import pprint

@generic
def format_for_leo(obj):
    """ Convert obj to string representiation (for editing in Leo)"""
    return pprint.pformat(obj)

@format_for_leo.when_type(list)
def format_list(obj):
    return "\n".join(str(s) for s in obj)

nodename_re = r'(@ipy?[\w-]+)?\s?(\w+)'

def all_cells():
    d = {}
    for p in c.allNodes_iter():
        h = p.headString()
        if h.startswith('@') and len(h.split()) == 1: 
            continue
        mo = re.match(nodename_re, h)
        if not mo:
            continue
        d[mo.group(2)] = p.copy()
    return d    
    

class LeoWorkbook:
    """ class to find cells """
    def __getattr__(self, key):
        cells = all_cells()
        p = cells[key]
        body = p.bodyString()
        return eval_body(body)
    def __setattr__(self,key,val):
        cells = all_cells()
        p = cells.get(key,None)
        if p is None:
            add_var(key,val)
        else:
            c.setBodyString(p,format_for_leo(val))
    def __str__(self):
        return "<LeoWorkbook>"
    __repr__ = __str__
ip.user_ns['nodes'] = LeoWorkbook()            

_dummyval = object()
@IPython.generics.complete_object.when_type(LeoWorkbook)
def workbook_complete(obj, prev):
    return all_cells().keys()
    

def add_var(varname, value = _dummyval):
    nodename = '@ipy-var ' + varname
    p2 = g.findNodeAnywhere(c,nodename)
    if not c.positionExists(p2):
        p2 = c.currentPosition().insertAfter()
        c.setHeadString(p2,'@ipy ' + varname)
        
    c.setCurrentPosition(p2)
    if value is _dummyval:
        val = ip.user_ns[varname]
    else:
        val = value
    formatted = format_for_leo(val)
    c.setBodyString(p2,formatted)

def add_file(self,fname):
    p2 = c.currentPosition().insertAfter()

def push_script(p):   
    script = g.getScript(c,p,useSelectedText=False,forcePythonSentinels=True,useSentinels=True)
    script = g.splitLines(script + '\n')
    script = ''.join(z for z in script if z.strip())
    ip.runlines(script)
    print "- Script end -"
    
def eval_body(body):
    try:
        val = ip.ev(body)
    except:
        # just use stringlist if it's not completely legal python expression
        val = IPython.genutils.SList(body.splitlines())
    return val 
    
def push_variable(p,varname):
    body = p.bodyString()
    val = eval_body(body.strip())
    ip.user_ns[varname] = val
    
def push_from_leo(p):
    # headstring without @ are just scripts
    if not p.headString().startswith('@'):
        push_script(p)
        return
    tup = p.headString().split(None,1)
    # @ipy foo is variable foo
    if len(tup) == 2 and tup[0] == '@ipy':
        varname = tup[1]
        push_variable(p,varname)
        return
    
ip.user_ns['leox'].push = push_from_leo    
    
def leo_f(self,s):
    ip = self.getapi()
    s = s.strip()
    if s in ip.user_ns:
        add_var(s)
    elif os.path.isfile(s):
        # todo open file
        pass

ip.expose_magic('leo',leo_f)
