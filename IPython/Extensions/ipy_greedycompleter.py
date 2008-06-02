""" Greedy completer extension for IPython

Normal tab completer refuses to evaluate nonsafe stuff. This will evaluate
everything, so you need to consider the consequences of pressing tab 
yourself!

Note that this extension simplifies readline interaction by setting
only whitespace as completer delimiter. If this works well, we will
do the same in default completer.

"""
from IPython import generics,ipapi
from IPython.genutils import dir2

def attr_matches(self, text):
    """Compute matches when text contains a dot.

    MONKEYPATCHED VERSION (ipy_greedycompleter.py)
    
    Assuming the text is of the form NAME.NAME....[NAME], and is
    evaluatable in self.namespace or self.global_namespace, it will be
    evaluated and its attributes (as revealed by dir()) are used as
    possible completions.  (For class instances, class members are are
    also considered.)

    WARNING: this can still invoke arbitrary C code, if an object
    with a __getattr__ hook is evaluated.

    """
    import re

    force_complete = 1
    # Another option, seems to work great. Catches things like ''.<tab>
    m = re.match(r"(\S+(\.\w+)*)\.(\w*)$", text)

    if m:
        expr, attr = m.group(1, 3)
    else:
        # force match - eval anything that ends with colon
        if not force_complete:
            return []
                
        m2 = re.match(r"(.+)\.(\w*)$", self.lbuf)
        if not m2:
            return []
        expr, attr = m2.group(1,2)
        
            
    try:        
        obj = eval(expr, self.namespace)
    except:
        try:
            obj = eval(expr, self.global_namespace)
        except:
            return []

    words = dir2(obj)
    
    try:
        words = generics.complete_object(obj, words)
    except ipapi.TryNext:
        pass
    # Build match list to return
    n = len(attr)
    res = ["%s.%s" % (expr, w) for w in words if w[:n] == attr ]
    return res

def main():
    import readline
    readline.set_completer_delims(" \n\t")
    # monkeypatch - the code will be folded to normal completer later on
    import IPython.completer
    IPython.completer.Completer.attr_matches = attr_matches

main()