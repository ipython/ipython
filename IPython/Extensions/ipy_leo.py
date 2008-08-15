""" ILeo - Leo plugin for IPython

   
"""
import IPython.ipapi
import IPython.genutils
import IPython.generics
from IPython.hooks import CommandChainDispatcher
import re
import UserDict
from IPython.ipapi import TryNext 
import IPython.macro
import IPython.Shell

_leo_push_history = set()

def init_ipython(ipy):
    """ This will be run by _ip.load('ipy_leo') 
    
    Leo still needs to run update_commander() after this.
    
    """
    global ip
    ip = ipy
    IPython.Shell.hijack_tk()
    ip.set_hook('complete_command', mb_completer, str_key = '%mb')
    ip.expose_magic('mb',mb_f)
    ip.expose_magic('lee',lee_f)
    ip.expose_magic('leoref',leoref_f)
    ip.expose_magic('lleo',lleo_f)    
    # Note that no other push command should EVER have lower than 0
    expose_ileo_push(push_mark_req, -1)
    expose_ileo_push(push_cl_node,100)
    # this should be the LAST one that will be executed, and it will never raise TryNext
    expose_ileo_push(push_ipython_script, 1000)
    expose_ileo_push(push_plain_python, 100)
    expose_ileo_push(push_ev_node, 100)
    ip.set_hook('pre_prompt_hook', ileo_pre_prompt_hook)     
    global wb
    wb = LeoWorkbook()
    ip.user_ns['wb'] = wb 
    

first_launch = True

def update_commander(new_leox):
    """ Set the Leo commander to use
    
    This will be run every time Leo does ipython-launch; basically,
    when the user switches the document he is focusing on, he should do
    ipython-launch to tell ILeo what document the commands apply to.
    
    """

    global first_launch
    if first_launch:
        show_welcome()
        first_launch = False

    global c,g
    c,g = new_leox.c, new_leox.g
    print "Set Leo Commander:",c.frame.getTitle()
    
    # will probably be overwritten by user, but handy for experimentation early on
    ip.user_ns['c'] = c
    ip.user_ns['g'] = g
    ip.user_ns['_leo'] = new_leox
    
    new_leox.push = push_position_from_leo
    run_leo_startup_node()

from IPython.external.simplegeneric import generic 
import pprint

def es(s):    
    g.es(s, tabName = 'IPython')
    pass

@generic
def format_for_leo(obj):
    """ Convert obj to string representiation (for editing in Leo)"""
    return pprint.pformat(obj)

# Just an example - note that this is a bad to actually do!
#@format_for_leo.when_type(list)
#def format_list(obj):
#    return "\n".join(str(s) for s in obj)
  

attribute_re = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')
def valid_attribute(s):
    return attribute_re.match(s)    

_rootnode = None
def rootnode():
    """ Get ileo root node (@ipy-root) 
    
    if node has become invalid or has not been set, return None
    
    Note that the root is the *first* @ipy-root item found    
    """
    global _rootnode
    if _rootnode is None:
        return None
    if c.positionExists(_rootnode.p):
        return _rootnode
    _rootnode = None
    return None  

def all_cells():
    global _rootnode
    d = {}
    r = rootnode() 
    if r is not None:
        nodes = r.p.children_iter()
    else:
        nodes = c.allNodes_iter()

    for p in nodes:
        h = p.headString()
        if h.strip() == '@ipy-root':
            # update root node (found it for the first time)
            _rootnode = LeoNode(p)            
            # the next recursive call will use the children of new root
            return all_cells()
        
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
    """ Node in Leo outline
    
    Most important attributes (getters/setters available:
     .v     - evaluate node, can also be alligned 
     .b, .h - body string, headline string
     .l     - value as string list
    
    Also supports iteration, 
    
    setitem / getitem (indexing):  
     wb.foo['key'] = 12
     assert wb.foo['key'].v == 12
    
    Note the asymmetry on setitem and getitem! Also other
    dict methods are available. 
    
    .ipush() - run push-to-ipython

    Minibuffer command access (tab completion works):
    
     mb save-to-file
    
    """
    def __init__(self,p):
        self.p = p.copy()

    def __str__(self):
        return "<LeoNode %s>" % str(self.p)
    
    __repr__ = __str__
    
    def __get_h(self): return self.p.headString()
    def __set_h(self,val):
        c.setHeadString(self.p,val)
        LeoNode.last_edited = self
        c.redraw()
        
    h = property( __get_h, __set_h, doc = "Node headline string")  

    def __get_b(self): return self.p.bodyString()
    def __set_b(self,val):
        c.setBodyString(self.p, val)
        LeoNode.last_edited = self
        c.redraw()
    
    b = property(__get_b, __set_b, doc = "Nody body string")
    
    def __set_val(self, val):        
        self.b = format_for_leo(val)
        
    v = property(lambda self: eval_node(self), __set_val, doc = "Node evaluated value")
    
    def __set_l(self,val):
        self.b = '\n'.join(val )
    l = property(lambda self : IPython.genutils.SList(self.b.splitlines()), 
                 __set_l, doc = "Node value as string list")
    
    def __iter__(self):
        """ Iterate through nodes direct children """
        
        return (LeoNode(p) for p in self.p.children_iter())

    def __children(self):
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
        d = self.__children()
        return d.keys()
    def __getitem__(self, key):
        """ wb.foo['Some stuff'] Return a child node with headline 'Some stuff'
        
        If key is a valid python name (e.g. 'foo'), look for headline '@k foo' as well
        """  
        key = str(key)
        d = self.__children()
        return d[key]
    def __setitem__(self, key, val):
        """ You can do wb.foo['My Stuff'] = 12 to create children 
        
        This will create 'My Stuff' as a child of foo (if it does not exist), and 
        do .v = 12 assignment.
        
        Exception:
        
        wb.foo['bar'] = 12
        
        will create a child with headline '@k bar', because bar is a valid python name
        and we don't want to crowd the WorkBook namespace with (possibly numerous) entries
        """
        key = str(key)
        d = self.__children()
        if key in d:
            d[key].v = val
            return
        
        if not valid_attribute(key):
            head = key
        else:
            head = '@k ' + key
        p = c.createLastChildNode(self.p, head, '')
        LeoNode(p).v = val
        
    def __delitem__(self, key):
        """ Remove child
        
        Allows stuff like wb.foo.clear() to remove all children
        """
        self[key].p.doDelete()
        c.redraw()
    
    def ipush(self):
        """ Does push-to-ipython on the node """
        push_from_leo(self)
        
    def go(self):
        """ Set node as current node (to quickly see it in Outline) """
        c.setCurrentPosition(self.p)
        c.redraw()
        
    def append(self):
        """ Add new node as the last child, return the new node """
        p = self.p.insertAsLastChild()
        return LeoNode(p)
        
        
    def script(self):
        """ Method to get the 'tangled' contents of the node
        
        (parse @others, << section >> references etc.)
        """
        return g.getScript(c,self.p,useSelectedText=False,useSentinels=False)
    
    def __get_uA(self):
        p = self.p
        # Create the uA if necessary.
        if not hasattr(p.v.t,'unknownAttributes'):
            p.v.t.unknownAttributes = {}        
        
        d = p.v.t.unknownAttributes.setdefault('ipython', {})
        return d        
    
    uA = property(__get_uA, doc = "Access persistent unknownAttributes of node")
        

class LeoWorkbook:
    """ class for 'advanced' node access 
    
    Has attributes for all "discoverable" nodes. Node is discoverable if it 
    either
    
    - has a valid python name (Foo, bar_12)
    - is a parent of an anchor node (if it has a child '@a foo', it is visible as foo)
    
    """
    def __getattr__(self, key):
        if key.startswith('_') or key == 'trait_names' or not valid_attribute(key):
            raise AttributeError
        cells = all_cells()
        p = cells.get(key, None)
        if p is None:
            return add_var(key)

        return LeoNode(p)

    def __str__(self):
        return "<LeoWorkbook>"
    def __setattr__(self,key, val):
        raise AttributeError("Direct assignment to workbook denied, try wb.%s.v = %s" % (key,val))
        
    __repr__ = __str__
    
    def __iter__(self):
        """ Iterate all (even non-exposed) nodes """
        cells = all_cells()
        return (LeoNode(p) for p in c.allNodes_iter())
    
    current = property(lambda self: LeoNode(c.currentPosition()), doc = "Currently selected node")
    
    def match_h(self, regex):
        cmp = re.compile(regex)
        for node in self:
            if re.match(cmp, node.h, re.IGNORECASE):
                yield node
        return
    
    def require(self, req):
        """ Used to control node push dependencies 
        
        Call this as first statement in nodes. If node has not been pushed, it will be pushed before proceeding
        
        E.g. wb.require('foo') will do wb.foo.ipush() if it hasn't been done already
        """
        
        if req not in _leo_push_history:
            es('Require: ' + req)
            getattr(self,req).ipush()
     

@IPython.generics.complete_object.when_type(LeoWorkbook)
def workbook_complete(obj, prev):
    return all_cells().keys() + [s for s in prev if not s.startswith('_')]
    

def add_var(varname):
    r = rootnode()
    try:
        if r is None:
            p2 = g.findNodeAnywhere(c,varname)
        else:
            p2 = g.findNodeInChildren(c, r.p, varname)
        if p2:
            return LeoNode(p2)

        if r is not None:
            p2 = r.p.insertAsLastChild()
        
        else:
            p2 =  c.currentPosition().insertAfter()
        
        c.setHeadString(p2,varname)
        return LeoNode(p2)
    finally:
        c.redraw()

def add_file(self,fname):
    p2 = c.currentPosition().insertAfter()

push_from_leo = CommandChainDispatcher()

def expose_ileo_push(f, prio = 0):
    push_from_leo.add(f, prio)

def push_ipython_script(node):
    """ Execute the node body in IPython, as if it was entered in interactive prompt """
    try:
        ohist = ip.IP.output_hist 
        hstart = len(ip.IP.input_hist)
        script = node.script()
                
        # The current node _p needs to handle wb.require() and recursive ipushes
        old_p = ip.user_ns.get('_p',None)
        ip.user_ns['_p'] = node
        ip.runlines(script)
        ip.user_ns['_p'] = old_p
        if old_p is None:
            del ip.user_ns['_p']
        
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
            es('ipy run: %s (%d LL)' %( node.h,len(script)))
    finally:
        c.redraw()

    
def eval_body(body):
    try:
        val = ip.ev(body)
    except:
        # just use stringlist if it's not completely legal python expression
        val = IPython.genutils.SList(body.splitlines())
    return val 
    
def push_plain_python(node):
    if not node.h.endswith('P'):
        raise TryNext
    script = node.script()
    lines = script.count('\n')
    try:
        exec script in ip.user_ns
    except:
        print " -- Exception in script:\n"+script + "\n --"
        raise
    es('ipy plain: %s (%d LL)' % (node.h,lines))
    

def push_cl_node(node):
    """ If node starts with @cl, eval it
    
    The result is put as last child of @ipy-results node, if it exists
    """
    if not node.b.startswith('@cl'):
        raise TryNext
        
    p2 = g.findNodeAnywhere(c,'@ipy-results')
    val = node.v
    if p2:
        es("=> @ipy-results")
        LeoNode(p2).v = val
    es(val)

def push_ev_node(node):
    """ If headline starts with @ev, eval it and put result in body """
    if not node.h.startswith('@ev '):
        raise TryNext
    expr = node.h.lstrip('@ev ')
    es('ipy eval ' + expr)
    res = ip.ev(expr)
    node.v = res
    
def push_mark_req(node):
    """ This should be the first one that gets called.
    
    It will mark the node as 'pushed', for wb.require.
    """
    _leo_push_history.add(node.h)
    raise TryNext
    
    
def push_position_from_leo(p):
    try:
        push_from_leo(LeoNode(p))
    except AttributeError,e:
        if e.args == ("Commands instance has no attribute 'frame'",):
            es("Error: ILeo not associated with .leo document")
            es("Press alt+shift+I to fix!")
        else:
            raise

@generic
def edit_object_in_leo(obj, varname):
    """ Make it @cl node so it can be pushed back directly by alt+I """
    node = add_var(varname)
    formatted = format_for_leo(obj)
    if not formatted.startswith('@cl'):
        formatted = '@cl\n' + formatted
    node.b = formatted 
    node.go()
    
@edit_object_in_leo.when_type(IPython.macro.Macro)
def edit_macro(obj,varname):
    bod = '_ip.defmacro("""\\\n' + obj.value + '""")'
    node = add_var('Macro_' + varname)
    node.b = bod
    node.go()

def get_history(hstart = 0):
    res = []
    ohist = ip.IP.output_hist 

    for idx in range(hstart, len(ip.IP.input_hist)):
        val = ohist.get(idx,None)
        has_output = True
        inp = ip.IP.input_hist_raw[idx]
        if inp.strip():
            res.append('In [%d]: %s' % (idx, inp))
        if val:
            res.append(pprint.pformat(val))
            res.append('\n')    
    return ''.join(res)
    
    
def lee_f(self,s):
    """ Open file(s)/objects in Leo
    
    - %lee hist -> open full session history in leo
    - Takes an object. l = [1,2,"hello"]; %lee l. Alt+I in leo pushes the object back
    - Takes an mglob pattern, e.g. '%lee *.cpp' or %lee 'rec:*.cpp'
    - Takes input history indices:  %lee 4 6-8 10 12-47
    """
    import os
        
    try:
        if s == 'hist':
            wb.ipython_history.b = get_history()
            wb.ipython_history.go()
            return
        
            
        if s and s[0].isdigit():
            # numbers; push input slices to leo
            lines = self.extract_input_slices(s.strip().split(), True)
            v = add_var('stored_ipython_input')
            v.b = '\n'.join(lines)
            return
            
        
        # try editing the object directly
        obj = ip.user_ns.get(s, None)
        if obj is not None:
            edit_object_in_leo(obj,s)
            return
     
        
        # if it's not object, it's a file name / mglob pattern
        from IPython.external import mglob
        
        files = (os.path.abspath(f) for f in mglob.expand(s))
        for fname in files:
            p = g.findNodeAnywhere(c,'@auto ' + fname)
            if not p:
                p = c.currentPosition().insertAfter()
            
            p.setHeadString('@auto ' + fname)
            if os.path.isfile(fname):
                c.setBodyString(p,open(fname).read())
            c.selectPosition(p)
        print "Editing file(s), press ctrl+shift+w in Leo to write @auto nodes"
    finally:
        c.redraw()

def leoref_f(self,s):
    """ Quick reference for ILeo """
    import textwrap
    print textwrap.dedent("""\
    %lee file/object - open file / object in leo
    %lleo Launch leo (use if you started ipython first!)
    wb.foo.v  - eval node foo (i.e. headstring is 'foo' or '@ipy foo')
    wb.foo.v = 12 - assign to body of node foo
    wb.foo.b - read or write the body of node foo
    wb.foo.l - body of node foo as string list
    
    for el in wb.foo:
      print el.v
       
    """
    )



def mb_f(self, arg):
    """ Execute leo minibuffer commands 
    
    Example:
     mb save-to-file
    """
    c.executeMinibufferCommand(arg)

def mb_completer(self,event):
    """ Custom completer for minibuffer """
    cmd_param = event.line.split()
    if event.line.endswith(' '):
        cmd_param.append('')
    if len(cmd_param) > 2:
        return ip.IP.Completer.file_matches(event.symbol)
    cmds = c.commandsDict.keys()
    cmds.sort()
    return cmds

def ileo_pre_prompt_hook(self):
    # this will fail if leo is not running yet
    try:
        c.outerUpdate()
    except NameError:
        pass
    raise TryNext
    


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
            push_from_leo(n)

def lleo_f(selg,  args):
    """ Launch leo from within IPython

    This command will return immediately when Leo has been
    launched, leaving a Leo session that is connected 
    with current IPython session (once you press alt+I in leo)

    Usage::
      lleo foo.leo
      lleo 
    """
    
    import shlex, sys
    argv = ['leo'] + shlex.split(args)
    sys.argv = argv
    # if this var exists and is true, leo will "launch" (connect)
    # ipython immediately when it's started
    global _request_immediate_connect
    _request_immediate_connect = True
    import leo.core.runLeo
    leo.core.runLeo.run()
