""" ILeo - Leo plugin for IPython

   
"""
import IPython.ipapi
import IPython.genutils
import IPython.generics
import re
import UserDict


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

attribute_re = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')
def valid_attribute(s):
    return attribute_re.match(s)    

def all_cells():
    d = {}
    for p in c.allNodes_iter():
        h = p.headString()
        if h.startswith('@a '):
            d[h.lstrip('@a ').strip()] = p.parent().copy()
        elif not valid_attribute(h):
            continue 
        d[h] = p.copy()
    return d    
    


def eval_node(n):
    body = n.b    
    if not body.startswith('@cl'):
        # plain python repr node, just eval it
        return ip.ev(n.b)
    # @cl nodes deserve special treatment - first eval the first line (minus cl), then use it to call the rest of body
    first, rest = body.split('\n',1)
    tup = first.split(None, 1)
    # @cl alone SPECIAL USE-> dump var to user_ns
    if len(tup) == 1:
        val = ip.ev(rest)
        ip.user_ns[n.h] = val
        es("%s = %s" % (n.h, repr(val)[:20]  )) 
        return val

    cl, hd = tup 

    xformer = ip.ev(hd.strip())
    es('Transform w/ %s' % repr(xformer))
    return xformer(rest, n)

class LeoNode(object, UserDict.DictMixin):
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
        self.b = format_for_leo(val)
        
    v = property(lambda self: eval_node(self), set_val)
    
    def set_l(self,val):
        self.b = '\n'.join(val )
    l = property(lambda self : IPython.genutils.SList(self.b.splitlines()), 
                 set_l)
    
    def __iter__(self):
        return (LeoNode(p) for p in self.p.children_iter())

    def _children(self):
        d = {}
        for child in self:
            head = child.h
            tup = head.split(None,1)
            if len(tup) > 1 and tup[0] == '@k':
                d[tup[1]] = child
                continue
            
            if not valid_attribute(head):
                d[head] = child
                continue
        return d
    def keys(self):
        d = self._children()
        return d.keys()
    def __getitem__(self, key):
        key = str(key)
        d = self._children()
        return d[key]
    def __setitem__(self, key, val):
        key = str(key)
        d = self._children()
        if key in d:
            d[key].v = val
            return
        
        if not valid_attribute(key):
            head = key
        else:
            head = '@k ' + key
        p = c.createLastChildNode(self.p, head, '')
        LeoNode(p).v = val
    def __delitem__(self,key):
        pass
        

class LeoWorkbook:
    """ class for 'advanced' node access """
    def __getattr__(self, key):
        if key.startswith('_') or key == 'trait_names' or not valid_attribute(key):
            raise AttributeError
        cells = all_cells()
        p = cells.get(key, None)
        if p is None:
            p = add_var(key)

        return LeoNode(p)

    def __str__(self):
        return "<LeoWorkbook>"
    def __setattr__(self,key, val):
        raise AttributeError("Direct assignment to workbook denied, try wb.%s.v = %s" % (key,val))
        
    __repr__ = __str__
ip.user_ns['wb'] = LeoWorkbook()



@IPython.generics.complete_object.when_type(LeoWorkbook)
def workbook_complete(obj, prev):
    return all_cells().keys()
    

def add_var(varname):
    c.beginUpdate()
    try:
        p2 = g.findNodeAnywhere(c,varname)
        if p2:
            return

        rootpos = g.findNodeAnywhere(c,'@ipy-results')
        if not rootpos:
            rootpos = c.currentPosition() 
        p2 = rootpos.insertAsLastChild()
        c.setHeadString(p2,varname)
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
            es('ipy run: %s (%d LL)' %( p.headString(),len(script)))
    finally:
        c.endUpdate()
    
    
def eval_body(body):
    try:
        val = ip.ev(body)
    except:
        # just use stringlist if it's not completely legal python expression
        val = IPython.genutils.SList(body.splitlines())
    return val 
    
def push_plain_python(p):
    script = g.getScript(c,p,useSelectedText=False,forcePythonSentinels=False,useSentinels=False)
    lines = script.count('\n')
    try:
        exec script in ip.user_ns
    except:
        print " -- Exception in script:\n"+script + "\n --"
        raise
    es('ipy plain: %s (%d LL)' % (p.headString(),lines))
    
def push_from_leo(p):
    nod = LeoNode(p)
    h =  p.headString()   
    if h.endswith('P'):
        push_plain_python(p)
        return
    if nod.b.startswith('@cl'):
        p2 = g.findNodeAnywhere(c,'@ipy-results')
        if p2:
            es("=> @ipy-results")
            LeoNode(p2).v = nod.v
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
    """ Quick reference for ILeo """
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
        print "Running @ipy-startup nodes"
        for n in LeoNode(p):
            push_from_leo(n.p)
            
            

run_leo_startup_node()
show_welcome()

