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

def es(s):    
    g.es(s, tabName = 'IPython')
    pass

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
    

class TrivialLeoWorkbook:
    """ class to find cells with simple syntax
    
    """
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
        return "<TrivialLeoWorkbook>"
    __repr__ = __str__

ip.user_ns['nodes'] = TrivialLeoWorkbook()            

def eval_node(n):
    body = n.b    
    if not body.startswith('@cl'):
        # plain python repr node, just eval it
        return ip.ev(n.b)
    # @cl nodes deserve special treatment - first eval the first line (minus cl), then use it to call the rest of body
    first, rest = body.split('\n',1)
    cl, hd = first.split(None, 1)
    if cl != '@cl':
        return None
    xformer = ip.ev(hd.strip())
    es('Transform w/ %s' % repr(xformer))
    return xformer(rest)
    
    

class LeoNode(object):
    def __init__(self,p):
        self.p = p.copy()

    def get_h(self): return self.p.headString()
    def set_h(self,val):
        print "set head",val
        c.beginUpdate() 
        try:
            c.setHeadString(self.p,val)
        finally:
            c.endUpdate()
        
    h = property( get_h, set_h)  

    def get_b(self): return self.p.bodyString()
    def set_b(self,val):
        print "set body",val
        c.beginUpdate()
        try: 
            c.setBodyString(self.p, val)
        finally:
            c.endUpdate()
    
    b = property(get_b, set_b)
    
    def set_val(self, val):
        self.b = pprint.pformat(val)
        
    v = property(lambda self: eval_node(self), set_val)
    
    def set_l(self,val):
        self.b = '\n'.join(val )
    l = property(lambda self : IPython.genutils.SList(self.b.splitlines()), 
                 set_l)
    
    def __iter__(self):
        return (LeoNode(p) for p in self.p.children_iter())
     

class LeoWorkbook:
    """ class for 'advanced' node access """
    def __getattr__(self, key):
        if key.startswith('_') or key == 'trait_names':
            raise AttributeError
        cells = all_cells()
        p = cells.get(key, None)
        if p is None:
            p = add_var(key,None)

        return LeoNode(p)

    def __str__(self):
        return "<LeoWorkbook>"
    __repr__ = __str__
ip.user_ns['wb'] = LeoWorkbook()


_dummyval = object()
@IPython.generics.complete_object.when_type(LeoWorkbook)
def workbook_complete(obj, prev):
    return all_cells().keys()
    

def add_var(varname, value = _dummyval):
    c.beginUpdate()
    try:
        
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
        if val is not None:
            formatted = format_for_leo(val)
            c.setBodyString(p2,formatted)
        return p2
    finally:
        c.endUpdate()

def add_file(self,fname):
    p2 = c.currentPosition().insertAfter()

def push_script(p):
    c.beginUpdate()
    try:
        ohist = ip.IP.output_hist 
        hstart = len(ip.IP.input_hist)
        script = g.getScript(c,p,useSelectedText=False,forcePythonSentinels=False,useSentinels=False)
        
        script = g.splitLines(script + '\n')
        script = ''.join(z for z in script if z.strip())
        
        ip.runlines(script)
        
        has_output = False
        for idx in range(hstart,len(ip.IP.input_hist)):
            val = ohist.get(idx,None)
            if val is None:
                continue
            has_output = True
            inp = ip.IP.input_hist[idx]
            if inp.strip():
                es('In: %s' % (inp[:40], ))
                
            es('<%d> %s' % (idx, pprint.pformat(ohist[idx],width = 40)))
        
        if not has_output:
            es('ipy run: %s' %( p.headString(),))
    finally:
        c.endUpdate()
    
    
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
    es('ipy var: %s' % (varname,))

def push_plain_python(p):
    script = g.getScript(c,p,useSelectedText=False,forcePythonSentinels=False,useSentinels=False)
    exec script in ip.user_ns
    es('ipy plain: %s' % (p.headString(),))
    
def push_from_leo(p):
    nod = LeoNode(p)
    h =  p.headString()   
    tup = h.split(None,1)
    # @ipy foo is variable foo
    if len(tup) == 2 and tup[0] == '@ipy':
        varname = tup[1]
        push_variable(p,varname)
        return
    if h.endswith('P'):
        push_plain_python(p)
        return
    if nod.b.startswith('@cl'):
        es(nod.v)
        return
    
    push_script(p)
    return
    
    
ip.user_ns['leox'].push = push_from_leo    
    
def leo_f(self,s):
    """ open file(s) in Leo
    
    Takes an mglob pattern, e.g. '%leo *.cpp' or %leo 'rec:*.cpp'  
    """
    import os
    from IPython.external import mglob
    
    files = mglob.expand(s)
    c.beginUpdate()
    try:
        for fname in files:
            p = g.findNodeAnywhere(c,'@auto ' + fname)
            if not p:
                p = c.currentPosition().insertAfter()
            
            p.setHeadString('@auto ' + fname)
            if os.path.isfile(fname):
                c.setBodyString(p,open(fname).read())
            c.selectPosition(p)
    finally:
        c.endUpdate()

ip.expose_magic('leo',leo_f)

def leoref_f(self,s):
    import textwrap
    print textwrap.dedent("""\
    %leo file - open file in leo
    wb.foo.v  - eval node foo (i.e. headstring is 'foo' or '@ipy foo')
    wb.foo.v = 12 - assign to body of node foo
    wb.foo.b - read or write the body of node foo
    wb.foo.l - body of node foo as string list
    
    for el in wb.foo:
      print el.v
       
    """
    )
ip.expose_magic('leoref',leoref_f)

def show_welcome():
    print "------------------"
    print "Welcome to Leo-enabled IPython session!"
    print "Try %leoref for quick reference."
    import IPython.platutils
    IPython.platutils.set_term_title('ILeo')
    IPython.platutils.freeze_term_title()

def run_leo_startup_node():
    p = g.findNodeAnywhere(c,'@ipy-startup')
    if p:
        print "Running @ipy-startup"
        push_script(p)

run_leo_startup_node()
show_welcome()

