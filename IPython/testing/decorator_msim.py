## The basic trick is to generate the source code for the decorated function
## with the right signature and to evaluate it.
## Uncomment the statement 'print >> sys.stderr, func_src'  in _decorate
## to understand what is going on.

__all__ = ["decorator", "update_wrapper", "getinfo"]

import inspect, sys
    
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

def update_wrapper(wrapper, wrapped, create=False):
    """
    An improvement over functools.update_wrapper. By default it works the
    same, but if the 'create' flag is set, generates a copy of the wrapper
    with the right signature and update the copy, not the original.
    Moreovoer, 'wrapped' can be a dictionary with keys 'name', 'doc', 'module',
    'dict', 'defaults'.
    """
    if isinstance(wrapped, dict):
        infodict = wrapped
    else: # assume wrapped is a function
        infodict = getinfo(wrapped)
    assert not '_wrapper_' in infodict["argnames"], \
           '"_wrapper_" is a reserved argument name!'
    if create: # create a brand new wrapper with the right signature
        src = "lambda %(signature)s: _wrapper_(%(signature)s)" % infodict
        # import sys; print >> sys.stderr, src # for debugging purposes
        wrapper = eval(src, dict(_wrapper_=wrapper))        
    try:
        wrapper.__name__ = infodict['name']
    except: # Python version < 2.4
        pass
    wrapper.__doc__ = infodict['doc']
    wrapper.__module__ = infodict['module']
    wrapper.__dict__.update(infodict['dict'])
    wrapper.func_defaults = infodict['defaults']
    return wrapper

# the real meat is here
def _decorator(caller, func):
    infodict = getinfo(func)
    argnames = infodict['argnames']
    assert not ('_call_' in argnames or '_func_' in argnames), \
           'You cannot use _call_ or _func_ as argument names!'
    src = "lambda %(signature)s: _call_(_func_, %(signature)s)" % infodict
    dec_func = eval(src, dict(_func_=func, _call_=caller))
    return update_wrapper(dec_func, func)

def decorator(caller, func=None):
    """
    General purpose decorator factory: takes a caller function as
    input and returns a decorator with the same attributes.
    A caller function is any function like this::

     def caller(func, *args, **kw):
         # do something
         return func(*args, **kw)
    
    Here is an example of usage:

    >>> @decorator
    ... def chatty(f, *args, **kw):
    ...     print "Calling %r" % f.__name__
    ...     return f(*args, **kw)

    >>> chatty.__name__
    'chatty'
    
    >>> @chatty
    ... def f(): pass
    ...
    >>> f()
    Calling 'f'

    For sake of convenience, the decorator factory can also be called with
    two arguments. In this casem ``decorator(caller, func)`` is just a
    shortcut for ``decorator(caller)(func)``.
    """
    if func is None: # return a decorator function
        return update_wrapper(lambda f : _decorator(caller, f), caller)
    else: # return a decorated function
        return _decorator(caller, func)

if __name__ == "__main__":
    import doctest; doctest.testmod()

#######################     LEGALESE    ##################################
      
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
