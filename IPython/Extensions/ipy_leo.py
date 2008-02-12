import IPython.ipapi
import IPython.genutils

ip = IPython.ipapi.get()
leo = ip.user_ns['leox']
c,g = leo.c, leo.g

from IPython.external.simplegeneric import generic 
import pprint

@generic
def format_for_leo(obj):
    """ Convert obj to string representiation (for editing in Leo)"""
    return pprint.pformat(obj)

@format_for_leo.when_type(list)
def format_list(obj):
    return '@ipy-type list\n' + "\n".join(str(s) for s in obj)


def add_var(self,varname):
    nodename = '@ipy-var ' + varname
    p2 = g.findNodeAnywhere(c,nodename)
    if not c.positionExists(p2):
        p2 = c.currentPosition().insertAfter()
        c.setHeadString(p2,'@ipy-var ' + varname)
        
    c.setCurrentPosition(p2)
    val = ip.user_ns[varname]
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
    print "eval",body
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
        add_var(self,s)
    elif os.path.isfile(s):
        # todo open file
        pass

ip.expose_magic('leo',leo_f)
