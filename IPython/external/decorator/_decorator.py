##########################     LICENCE     ###############################
##
##   Copyright (c) 2005, Michele Simionato
##   All rights reserved.
##
##   Redistributions of source code must retain the above copyright
##   notice, this list of conditions and the following disclaimer.
##   Redistributions in bytecode form must reproduce the above copyright
##   notice, this list of conditions and the following disclaimer in
##   the documentation and/or other materials provided with the
##   distribution.

##   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
##   "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
##   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
##   A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
##   HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
##   INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
##   BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
##   OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
##   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
##   TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
##   USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
##   DAMAGE.

"""
Decorator module, see http://pypi.python.org/pypi/decorator
for the documentation.
"""

__all__ = ["decorator", "FunctionMaker", "partial",
           "deprecated", "getinfo", "new_wrapper"]

import os, sys, re, inspect, string, warnings
try:
    from functools import partial
except ImportError: # for Python version < 2.5
    class partial(object):
        "A simple replacement of functools.partial"
        def __init__(self, func, *args, **kw):
            self.func = func
            self.args = args
            self.keywords = kw
        def __call__(self, *otherargs, **otherkw):
            kw = self.keywords.copy()
            kw.update(otherkw)
            return self.func(*(self.args + otherargs), **kw)

DEF = re.compile('\s*def\s*([_\w][_\w\d]*)\s*\(')

# basic functionality
class FunctionMaker(object):
    """
    An object with the ability to create functions with a given signature.
    It has attributes name, doc, module, signature, defaults, dict and
    methods update and make.
    """
    def __init__(self, func=None, name=None, signature=None,
                 defaults=None, doc=None, module=None, funcdict=None):
        if func:
            # func can be a class or a callable, but not an instance method
            self.name = func.__name__
            if self.name == '<lambda>': # small hack for lambda functions
                self.name = '_lambda_'
            self.doc = func.__doc__
            self.module = func.__module__
            if inspect.isfunction(func):
                argspec = inspect.getargspec(func)
                self.args, self.varargs, self.keywords, self.defaults = argspec
                for i, arg in enumerate(self.args):
                    setattr(self, 'arg%d' % i, arg)
                self.signature = inspect.formatargspec(
                    formatvalue=lambda val: "", *argspec)[1:-1]
                self.dict = func.__dict__.copy()
        if name:
            self.name = name
        if signature is not None:
            self.signature = signature
        if defaults:
            self.defaults = defaults
        if doc:
            self.doc = doc
        if module:
            self.module = module
        if funcdict:
            self.dict = funcdict
        # check existence required attributes
        assert hasattr(self, 'name')
        if not hasattr(self, 'signature'):
            raise TypeError('You are decorating a non function: %s' % func)

    def update(self, func, **kw):
        "Update the signature of func with the data in self"
        func.__name__ = self.name
        func.__doc__ = getattr(self, 'doc', None)
        func.__dict__ = getattr(self, 'dict', {})
        func.func_defaults = getattr(self, 'defaults', ())
        callermodule = sys._getframe(3).f_globals.get('__name__', '?')
        func.__module__ = getattr(self, 'module', callermodule)
        func.__dict__.update(kw)

    def make(self, src_templ, evaldict=None, addsource=False, **attrs):
        "Make a new function from a given template and update the signature"
        src = src_templ % vars(self) # expand name and signature
        evaldict = evaldict or {}
        mo = DEF.match(src)
        if mo is None:
            raise SyntaxError('not a valid function template\n%s' % src)
        name = mo.group(1) # extract the function name
        reserved_names = set([name] + [
            arg.strip(' *') for arg in self.signature.split(',')])
        for n, v in evaldict.iteritems():
            if n in reserved_names:
                raise NameError('%s is overridden in\n%s' % (n, src))
        if not src.endswith('\n'): # add a newline just for safety
            src += '\n'
        try:
            code = compile(src, '<string>', 'single')
            exec code in evaldict
        except:
            print >> sys.stderr, 'Error in generated code:'
            print >> sys.stderr, src
            raise
        func = evaldict[name]
        if addsource:
            attrs['__source__'] = src
        self.update(func, **attrs)
        return func

    @classmethod
    def create(cls, obj, body, evaldict, defaults=None,
               doc=None, module=None, addsource=True,**attrs):
        """
        Create a function from the strings name, signature and body.
        evaldict is the evaluation dictionary. If addsource is true an attribute
        __source__ is added to the result. The attributes attrs are added,
        if any.
        """
        if isinstance(obj, str): # "name(signature)"
            name, rest = obj.strip().split('(', 1)
            signature = rest[:-1] #strip a right parens
            func = None
        else: # a function
            name = None
            signature = None
            func = obj
        fun = cls(func, name, signature, defaults, doc, module)
        ibody = '\n'.join('    ' + line for line in body.splitlines())
        return fun.make('def %(name)s(%(signature)s):\n' + ibody,
                        evaldict, addsource, **attrs)

def decorator(caller, func=None):
    """
    decorator(caller) converts a caller function into a decorator;
    decorator(caller, func) decorates a function using a caller.
    """
    if func is not None: # returns a decorated function
        return FunctionMaker.create(
            func, "return _call_(_func_, %(signature)s)",
            dict(_call_=caller, _func_=func), undecorated=func)
    else: # returns a decorator
        if isinstance(caller, partial):
            return partial(decorator, caller)
        # otherwise assume caller is a function
        f = inspect.getargspec(caller)[0][0] # first arg
        return FunctionMaker.create(
            '%s(%s)' % (caller.__name__, f),
            'return decorator(_call_, %s)' % f,
            dict(_call_=caller, decorator=decorator), undecorated=caller,
            doc=caller.__doc__, module=caller.__module__)

###################### deprecated functionality #########################

@decorator
def deprecated(func, *args, **kw):
    "A decorator for deprecated functions"
    warnings.warn(
        ('Calling the deprecated function %r\n'
         'Downgrade to decorator 2.3 if you want to use this functionality')
        % func.__name__, DeprecationWarning, stacklevel=3)
    return func(*args, **kw)

@deprecated
def getinfo(func):
    """
    Returns an info dictionary containing:
    - name (the name of the function : str)
    - argnames (the names of the arguments : list)
    - defaults (the values of the default arguments : tuple)
    - signature (the signature : str)
    - doc (the docstring : str)
    - module (the module name : str)
    - dict (the function __dict__ : str)

    >>> def f(self, x=1, y=2, *args, **kw): pass

    >>> info = getinfo(f)

    >>> info["name"]
    'f'
    >>> info["argnames"]
    ['self', 'x', 'y', 'args', 'kw']

    >>> info["defaults"]
    (1, 2)

    >>> info["signature"]
    'self, x, y, *args, **kw'
    """
    assert inspect.ismethod(func) or inspect.isfunction(func)
    regargs, varargs, varkwargs, defaults = inspect.getargspec(func)
    argnames = list(regargs)
    if varargs:
        argnames.append(varargs)
    if varkwargs:
        argnames.append(varkwargs)
    signature = inspect.formatargspec(regargs, varargs, varkwargs, defaults,
                                      formatvalue=lambda value: "")[1:-1]
    return dict(name=func.__name__, argnames=argnames, signature=signature,
                defaults = func.func_defaults, doc=func.__doc__,
                module=func.__module__, dict=func.__dict__,
                globals=func.func_globals, closure=func.func_closure)

@deprecated
def update_wrapper(wrapper, model, infodict=None):
    "A replacement for functools.update_wrapper"
    infodict = infodict or getinfo(model)
    wrapper.__name__ = infodict['name']
    wrapper.__doc__ = infodict['doc']
    wrapper.__module__ = infodict['module']
    wrapper.__dict__.update(infodict['dict'])
    wrapper.func_defaults = infodict['defaults']
    wrapper.undecorated = model
    return wrapper

@deprecated
def new_wrapper(wrapper, model):
    """
    An improvement over functools.update_wrapper. The wrapper is a generic
    callable object. It works by generating a copy of the wrapper with the
    right signature and by updating the copy, not the original.
    Moreovoer, 'model' can be a dictionary with keys 'name', 'doc', 'module',
    'dict', 'defaults'.
    """
    if isinstance(model, dict):
        infodict = model
    else: # assume model is a function
        infodict = getinfo(model)
    assert not '_wrapper_' in infodict["argnames"], (
        '"_wrapper_" is a reserved argument name!')
    src = "lambda %(signature)s: _wrapper_(%(signature)s)" % infodict
    funcopy = eval(src, dict(_wrapper_=wrapper))
    return update_wrapper(funcopy, model, infodict)

