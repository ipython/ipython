# This is a modified copy of parts of inspect.py from Python 3.11
# https://github.com/python/cpython/blob/2d5f4ba17480c1f883a0822c90af25d2ec9bf7ed/Lib/inspect.py



import types
from collections import OrderedDict

# TODO get_annotations also calls repr!
from inspect import isbuiltin, ismethoddescriptor, isclass, ismodule, isfunction, CO_VARARGS, CO_VARKEYWORDS, unwrap, _empty, _void
import inspect
from keyword import iskeyword
import tokenize
import token
import ast
import sys
import itertools
import functools
import enum
import re

def safe_repr(obj):
    return 'SAFE_REPR'

###########################
## Begin modified copy of https://github.com/python/cpython/blob/2d5f4ba17480c1f883a0822c90af25d2ec9bf7ed/Lib/inspect.py
###########################


def get_annotations(obj, *, globals=None, locals=None, eval_str=False):
    """Compute the annotations dict for an object.
    obj may be a callable, class, or module.
    Passing in an object of any other type raises TypeError.
    Returns a dict.  get_annotations() returns a new dict every time
    it's called; calling it twice on the same object will return two
    different but equivalent dicts.
    This function handles several details for you:
      * If eval_str is true, values of type str will
        be un-stringized using eval().  This is intended
        for use with stringized annotations
        ("from __future__ import annotations").
      * If obj doesn't have an annotations dict, returns an
        empty dict.  (Functions and methods always have an
        annotations dict; classes, modules, and other types of
        callables may not.)
      * Ignores inherited annotations on classes.  If a class
        doesn't have its own annotations dict, returns an empty dict.
      * All accesses to object members and dict values are done
        using getattr() and dict.get() for safety.
      * Always, always, always returns a freshly-created dict.
    eval_str controls whether or not values of type str are replaced
    with the result of calling eval() on those values:
      * If eval_str is true, eval() is called on values of type str.
      * If eval_str is false (the default), values of type str are unchanged.
    globals and locals are passed in to eval(); see the documentation
    for eval() for more information.  If either globals or locals is
    None, this function may replace that value with a context-specific
    default, contingent on type(obj):
      * If obj is a module, globals defaults to obj.__dict__.
      * If obj is a class, globals defaults to
        sys.modules[obj.__module__].__dict__ and locals
        defaults to the obj class namespace.
      * If obj is a callable, globals defaults to obj.__globals__,
        although if obj is a wrapped function (using
        functools.update_wrapper()) it is first unwrapped.
    """
    if isinstance(obj, type):
        # class
        obj_dict = getattr(obj, '__dict__', None)
        if obj_dict and hasattr(obj_dict, 'get'):
            ann = obj_dict.get('__annotations__', None)
            if isinstance(ann, types.GetSetDescriptorType):
                ann = None
        else:
            ann = None

        obj_globals = None
        module_name = getattr(obj, '__module__', None)
        if module_name:
            module = sys.modules.get(module_name, None)
            if module:
                obj_globals = getattr(module, '__dict__', None)
        obj_locals = dict(vars(obj))
        unwrap = obj
    elif isinstance(obj, types.ModuleType):
        # module
        ann = getattr(obj, '__annotations__', None)
        obj_globals = getattr(obj, '__dict__')
        obj_locals = None
        unwrap = None
    elif callable(obj):
        # this includes types.Function, types.BuiltinFunctionType,
        # types.BuiltinMethodType, functools.partial, functools.singledispatch,
        # "class funclike" from Lib/test/test_inspect... on and on it goes.
        ann = getattr(obj, '__annotations__', None)
        obj_globals = getattr(obj, '__globals__', None)
        obj_locals = None
        unwrap = obj
    else:
        raise TypeError(f"{obj!r} is not a module, class, or callable.")

    if ann is None:
        return {}

    if not isinstance(ann, dict):
        raise ValueError(f"{obj!r}.__annotations__ is neither a dict nor None")

    if not ann:
        return {}

    if not eval_str:
        return dict(ann)

    if unwrap is not None:
        while True:
            if hasattr(unwrap, '__wrapped__'):
                unwrap = unwrap.__wrapped__
                continue
            if isinstance(unwrap, functools.partial):
                unwrap = unwrap.func
                continue
            break
        if hasattr(unwrap, "__globals__"):
            obj_globals = unwrap.__globals__

    if globals is None:
        globals = obj_globals
    if locals is None:
        locals = obj_locals

    return_value = {key:
        value if not isinstance(value, str) else eval(value, globals, locals)
        for key, value in ann.items() }
    return return_value

def formatannotation(annotation, base_module=None):
    if getattr(annotation, '__module__', None) == 'typing':
        def repl(match):
            text = match.group()
            return text.removeprefix('typing.')
        return re.sub(r'[\w\.]+', repl, repr(annotation))
    if isinstance(annotation, types.GenericAlias):
        return str(annotation)
    if isinstance(annotation, type):
        if annotation.__module__ in ('builtins', base_module):
            return annotation.__qualname__
        return annotation.__module__+'.'+annotation.__qualname__
    return repr(annotation)


###############################################################################
### Function Signature Object (PEP 362)
###############################################################################


_NonUserDefinedCallables = (types.WrapperDescriptorType,
                            types.MethodWrapperType,
                            types.ClassMethodDescriptorType,
                            types.BuiltinFunctionType)


def _signature_get_user_defined_method(cls, method_name):
    """Private helper. Checks if ``cls`` has an attribute
    named ``method_name`` and returns it only if it is a
    pure python function.
    """
    try:
        meth = getattr(cls, method_name)
    except AttributeError:
        return
    else:
        if not isinstance(meth, _NonUserDefinedCallables):
            # Once '__signature__' will be added to 'C'-level
            # callables, this check won't be necessary
            return meth


def _signature_get_partial(wrapped_sig, partial, extra_args=()):
    """Private helper to calculate how 'wrapped_sig' signature will
    look like after applying a 'functools.partial' object (or alike)
    on it.
    """

    old_params = wrapped_sig.parameters
    new_params = OrderedDict(old_params.items())

    partial_args = partial.args or ()
    partial_keywords = partial.keywords or {}

    if extra_args:
        partial_args = extra_args + partial_args

    try:
        ba = wrapped_sig.bind_partial(*partial_args, **partial_keywords)
    except TypeError as ex:
        msg = 'partial object {!r} has incorrect arguments'.format(partial)
        raise ValueError(msg) from ex


    transform_to_kwonly = False
    for param_name, param in old_params.items():
        try:
            arg_value = ba.arguments[param_name]
        except KeyError:
            pass
        else:
            if param.kind is _POSITIONAL_ONLY:
                # If positional-only parameter is bound by partial,
                # it effectively disappears from the signature
                new_params.pop(param_name)
                continue

            if param.kind is _POSITIONAL_OR_KEYWORD:
                if param_name in partial_keywords:
                    # This means that this parameter, and all parameters
                    # after it should be keyword-only (and var-positional
                    # should be removed). Here's why. Consider the following
                    # function:
                    #     foo(a, b, *args, c):
                    #         pass
                    #
                    # "partial(foo, a='spam')" will have the following
                    # signature: "(*, a='spam', b, c)". Because attempting
                    # to call that partial with "(10, 20)" arguments will
                    # raise a TypeError, saying that "a" argument received
                    # multiple values.
                    transform_to_kwonly = True
                    # Set the new default value
                    new_params[param_name] = param.replace(default=arg_value)
                else:
                    # was passed as a positional argument
                    new_params.pop(param.name)
                    continue

            if param.kind is _KEYWORD_ONLY:
                # Set the new default value
                new_params[param_name] = param.replace(default=arg_value)

        if transform_to_kwonly:
            assert param.kind is not _POSITIONAL_ONLY

            if param.kind is _POSITIONAL_OR_KEYWORD:
                new_param = new_params[param_name].replace(kind=_KEYWORD_ONLY)
                new_params[param_name] = new_param
                new_params.move_to_end(param_name)
            elif param.kind in (_KEYWORD_ONLY, _VAR_KEYWORD):
                new_params.move_to_end(param_name)
            elif param.kind is _VAR_POSITIONAL:
                new_params.pop(param.name)

    return wrapped_sig.replace(parameters=new_params.values())


def _signature_bound_method(sig):
    """Private helper to transform signatures for unbound
    functions to bound methods.
    """

    params = tuple(sig.parameters.values())

    if not params or params[0].kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
        raise ValueError('invalid method signature')

    kind = params[0].kind
    if kind in (_POSITIONAL_OR_KEYWORD, _POSITIONAL_ONLY):
        # Drop first parameter:
        # '(p1, p2[, ...])' -> '(p2[, ...])'
        params = params[1:]
    else:
        if kind is not _VAR_POSITIONAL:
            # Unless we add a new parameter type we never
            # get here
            raise ValueError('invalid argument type')
        # It's a var-positional parameter.
        # Do nothing. '(*args[, ...])' -> '(*args[, ...])'

    return sig.replace(parameters=params)


def _signature_is_builtin(obj):
    """Private helper to test if `obj` is a callable that might
    support Argument Clinic's __text_signature__ protocol.
    """
    return (isbuiltin(obj) or
            ismethoddescriptor(obj) or
            isinstance(obj, _NonUserDefinedCallables) or
            # Can't test 'isinstance(type)' here, as it would
            # also be True for regular python classes
            obj in (type, object))


def _signature_is_functionlike(obj):
    """Private helper to test if `obj` is a duck type of FunctionType.
    A good example of such objects are functions compiled with
    Cython, which have all attributes that a pure Python function
    would have, but have their code statically compiled.
    """

    if not callable(obj) or isclass(obj):
        # All function-like objects are obviously callables,
        # and not classes.
        return False

    name = getattr(obj, '__name__', None)
    code = getattr(obj, '__code__', None)
    defaults = getattr(obj, '__defaults__', _void) # Important to use _void ...
    kwdefaults = getattr(obj, '__kwdefaults__', _void) # ... and not None here
    annotations = getattr(obj, '__annotations__', None)

    return (isinstance(code, types.CodeType) and
            isinstance(name, str) and
            (defaults is None or isinstance(defaults, tuple)) and
            (kwdefaults is None or isinstance(kwdefaults, dict)) and
            (isinstance(annotations, (dict)) or annotations is None) )


def _signature_strip_non_python_syntax(signature):
    """
    Private helper function. Takes a signature in Argument Clinic's
    extended signature format.
    Returns a tuple of three things:
      * that signature re-rendered in standard Python syntax,
      * the index of the "self" parameter (generally 0), or None if
        the function does not have a "self" parameter, and
      * the index of the last "positional only" parameter,
        or None if the signature has no positional-only parameters.
    """

    if not signature:
        return signature, None, None

    self_parameter = None
    last_positional_only = None

    lines = [l.encode('ascii') for l in signature.split('\n')]
    generator = iter(lines).__next__
    token_stream = tokenize.tokenize(generator)

    delayed_comma = False
    skip_next_comma = False
    text = []
    add = text.append

    current_parameter = 0
    OP = token.OP
    ERRORTOKEN = token.ERRORTOKEN

    # token stream always starts with ENCODING token, skip it
    t = next(token_stream)
    assert t.type == tokenize.ENCODING

    for t in token_stream:
        type, string = t.type, t.string

        if type == OP:
            if string == ',':
                if skip_next_comma:
                    skip_next_comma = False
                else:
                    assert not delayed_comma
                    delayed_comma = True
                    current_parameter += 1
                continue

            if string == '/':
                assert not skip_next_comma
                assert last_positional_only is None
                skip_next_comma = True
                last_positional_only = current_parameter - 1
                continue

        if (type == ERRORTOKEN) and (string == '$'):
            assert self_parameter is None
            self_parameter = current_parameter
            continue

        if delayed_comma:
            delayed_comma = False
            if not ((type == OP) and (string == ')')):
                add(', ')
        add(string)
        if (string == ','):
            add(' ')
    clean_signature = ''.join(text)
    return clean_signature, self_parameter, last_positional_only


def _signature_fromstr(cls, obj, s, skip_bound_arg=True):
    """Private helper to parse content of '__text_signature__'
    and return a Signature based on it.
    """
    Parameter = cls._parameter_cls

    clean_signature, self_parameter, last_positional_only = \
        _signature_strip_non_python_syntax(s)

    program = "def foo" + clean_signature + ": pass"

    try:
        module = ast.parse(program)
    except SyntaxError:
        module = None

    if not isinstance(module, ast.Module):
        raise ValueError("{!r} builtin has invalid signature".format(obj))

    f = module.body[0]

    parameters = []
    empty = Parameter.empty
    invalid = object()

    module = None
    module_dict = {}
    module_name = getattr(obj, '__module__', None)
    if module_name:
        module = sys.modules.get(module_name, None)
        if module:
            module_dict = module.__dict__
    sys_module_dict = sys.modules.copy()

    def parse_name(node):
        assert isinstance(node, ast.arg)
        if node.annotation is not None:
            raise ValueError("Annotations are not currently supported")
        return node.arg

    def wrap_value(s):
        try:
            value = eval(s, module_dict)
        except NameError:
            try:
                value = eval(s, sys_module_dict)
            except NameError:
                raise RuntimeError()

        if isinstance(value, (str, int, float, bytes, bool, type(None))):
            return ast.Constant(value)
        raise RuntimeError()

    class RewriteSymbolics(ast.NodeTransformer):
        def visit_Attribute(self, node):
            a = []
            n = node
            while isinstance(n, ast.Attribute):
                a.append(n.attr)
                n = n.value
            if not isinstance(n, ast.Name):
                raise RuntimeError()
            a.append(n.id)
            value = ".".join(reversed(a))
            return wrap_value(value)

        def visit_Name(self, node):
            if not isinstance(node.ctx, ast.Load):
                raise ValueError()
            return wrap_value(node.id)

    def p(name_node, default_node, default=empty):
        name = parse_name(name_node)
        if name is invalid:
            return None
        if default_node and default_node is not _empty:
            try:
                default_node = RewriteSymbolics().visit(default_node)
                o = ast.literal_eval(default_node)
            except ValueError:
                o = invalid
            if o is invalid:
                return None
            default = o if o is not invalid else default
        parameters.append(Parameter(name, kind, default=default, annotation=empty))

    # non-keyword-only parameters
    args = reversed(f.args.args)
    defaults = reversed(f.args.defaults)
    iter = itertools.zip_longest(args, defaults, fillvalue=None)
    if last_positional_only is not None:
        kind = Parameter.POSITIONAL_ONLY
    else:
        kind = Parameter.POSITIONAL_OR_KEYWORD
    for i, (name, default) in enumerate(reversed(list(iter))):
        p(name, default)
        if i == last_positional_only:
            kind = Parameter.POSITIONAL_OR_KEYWORD

    # *args
    if f.args.vararg:
        kind = Parameter.VAR_POSITIONAL
        p(f.args.vararg, empty)

    # keyword-only arguments
    kind = Parameter.KEYWORD_ONLY
    for name, default in zip(f.args.kwonlyargs, f.args.kw_defaults):
        p(name, default)

    # **kwargs
    if f.args.kwarg:
        kind = Parameter.VAR_KEYWORD
        p(f.args.kwarg, empty)

    if self_parameter is not None:
        # Possibly strip the bound argument:
        #    - We *always* strip first bound argument if
        #      it is a module.
        #    - We don't strip first bound argument if
        #      skip_bound_arg is False.
        assert parameters
        _self = getattr(obj, '__self__', None)
        self_isbound = _self is not None
        self_ismodule = ismodule(_self)
        if self_isbound and (self_ismodule or skip_bound_arg):
            parameters.pop(0)
        else:
            # for builtins, self parameter is always positional-only!
            p = parameters[0].replace(kind=Parameter.POSITIONAL_ONLY)
            parameters[0] = p

    return cls(parameters, return_annotation=cls.empty)


def _signature_from_builtin(cls, func, skip_bound_arg=True):
    """Private helper function to get signature for
    builtin callables.
    """

    if not _signature_is_builtin(func):
        raise TypeError("{!r} is not a Python builtin "
                        "function".format(func))

    s = getattr(func, "__text_signature__", None)
    if not s:
        raise ValueError("no signature found for builtin {!r}".format(func))

    return _signature_fromstr(cls, func, s, skip_bound_arg)


def _signature_from_function(cls, func, skip_bound_arg=True,
                             globals=None, locals=None, eval_str=False):
    """Private helper: constructs Signature for the given python function."""

    is_duck_function = False
    if not isfunction(func):
        if _signature_is_functionlike(func):
            is_duck_function = True
        else:
            # If it's not a pure Python function, and not a duck type
            # of pure function:
            raise TypeError('{!r} is not a Python function'.format(func))

    s = getattr(func, "__text_signature__", None)
    if s:
        return _signature_fromstr(cls, func, s, skip_bound_arg)

    Parameter = cls._parameter_cls

    # Parameter information.
    func_code = func.__code__
    pos_count = func_code.co_argcount
    arg_names = func_code.co_varnames
    posonly_count = func_code.co_posonlyargcount
    positional = arg_names[:pos_count]
    keyword_only_count = func_code.co_kwonlyargcount
    keyword_only = arg_names[pos_count:pos_count + keyword_only_count]
    annotations = get_annotations(func, globals=globals, locals=locals, eval_str=eval_str)
    defaults = func.__defaults__
    kwdefaults = func.__kwdefaults__

    if defaults:
        pos_default_count = len(defaults)
    else:
        pos_default_count = 0

    parameters = []

    non_default_count = pos_count - pos_default_count
    posonly_left = posonly_count

    # Non-keyword-only parameters w/o defaults.
    for name in positional[:non_default_count]:
        kind = _POSITIONAL_ONLY if posonly_left else _POSITIONAL_OR_KEYWORD
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=kind))
        if posonly_left:
            posonly_left -= 1

    # ... w/ defaults.
    for offset, name in enumerate(positional[non_default_count:]):
        kind = _POSITIONAL_ONLY if posonly_left else _POSITIONAL_OR_KEYWORD
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=kind,
                                    default=defaults[offset]))
        if posonly_left:
            posonly_left -= 1

    # *args
    if func_code.co_flags & CO_VARARGS:
        name = arg_names[pos_count + keyword_only_count]
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=_VAR_POSITIONAL))

    # Keyword-only parameters.
    for name in keyword_only:
        default = _empty
        if kwdefaults is not None:
            default = kwdefaults.get(name, _empty)

        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=_KEYWORD_ONLY,
                                    default=default))
    # **kwargs
    if func_code.co_flags & CO_VARKEYWORDS:
        index = pos_count + keyword_only_count
        if func_code.co_flags & CO_VARARGS:
            index += 1

        name = arg_names[index]
        annotation = annotations.get(name, _empty)
        parameters.append(Parameter(name, annotation=annotation,
                                    kind=_VAR_KEYWORD))

    # Is 'func' is a pure Python function - don't validate the
    # parameters list (for correct order and defaults), it should be OK.
    return cls(parameters,
               return_annotation=annotations.get('return', _empty),
               __validate_parameters__=is_duck_function)


def _signature_from_callable(obj, *,
                             follow_wrapper_chains=True,
                             skip_bound_arg=True,
                             globals=None,
                             locals=None,
                             eval_str=False,
                             sigcls):

    """Private helper function to get signature for arbitrary
    callable objects.
    """

    _get_signature_of = functools.partial(_signature_from_callable,
                                follow_wrapper_chains=follow_wrapper_chains,
                                skip_bound_arg=skip_bound_arg,
                                globals=globals,
                                locals=locals,
                                sigcls=sigcls,
                                eval_str=eval_str)

    if not callable(obj):
        raise TypeError('{!r} is not a callable object'.format(obj))

    if isinstance(obj, types.MethodType):
        # In this case we skip the first parameter of the underlying
        # function (usually `self` or `cls`).
        sig = _get_signature_of(obj.__func__)

        if skip_bound_arg:
            return _signature_bound_method(sig)
        else:
            return sig

    # Was this function wrapped by a decorator?
    if follow_wrapper_chains:
        # Unwrap until we find an explicit signature or a MethodType (which will be
        # handled explicitly below).
        obj = unwrap(obj, stop=(lambda f: hasattr(f, "__signature__")
                                or isinstance(f, types.MethodType)))
        if isinstance(obj, types.MethodType):
            # If the unwrapped object is a *method*, we might want to
            # skip its first parameter (self).
            # See test_signature_wrapped_bound_method for details.
            return _get_signature_of(obj)

    try:
        sig = obj.__signature__
    except AttributeError:
        pass
    else:
        if sig is not None:
            if not isinstance(sig, Signature):
                raise TypeError(
                    'unexpected object {!r} in __signature__ '
                    'attribute'.format(sig))
            return sig

    try:
        partialmethod = obj._partialmethod
    except AttributeError:
        pass
    else:
        if isinstance(partialmethod, functools.partialmethod):
            # Unbound partialmethod (see functools.partialmethod)
            # This means, that we need to calculate the signature
            # as if it's a regular partial object, but taking into
            # account that the first positional argument
            # (usually `self`, or `cls`) will not be passed
            # automatically (as for boundmethods)

            wrapped_sig = _get_signature_of(partialmethod.func)

            sig = _signature_get_partial(wrapped_sig, partialmethod, (None,))
            first_wrapped_param = tuple(wrapped_sig.parameters.values())[0]
            if first_wrapped_param.kind is Parameter.VAR_POSITIONAL:
                # First argument of the wrapped callable is `*args`, as in
                # `partialmethod(lambda *args)`.
                return sig
            else:
                sig_params = tuple(sig.parameters.values())
                assert (not sig_params or
                        first_wrapped_param is not sig_params[0])
                new_params = (first_wrapped_param,) + sig_params
                return sig.replace(parameters=new_params)

    if isfunction(obj) or _signature_is_functionlike(obj):
        # If it's a pure Python function, or an object that is duck type
        # of a Python function (Cython functions, for instance), then:
        return _signature_from_function(sigcls, obj,
                                        skip_bound_arg=skip_bound_arg,
                                        globals=globals, locals=locals, eval_str=eval_str)

    if _signature_is_builtin(obj):
        return _signature_from_builtin(sigcls, obj,
                                       skip_bound_arg=skip_bound_arg)

    if isinstance(obj, functools.partial):
        wrapped_sig = _get_signature_of(obj.func)
        return _signature_get_partial(wrapped_sig, obj)

    sig = None
    if isinstance(obj, type):
        # obj is a class or a metaclass

        # First, let's see if it has an overloaded __call__ defined
        # in its metaclass
        call = _signature_get_user_defined_method(type(obj), '__call__')
        if call is not None:
            sig = _get_signature_of(call)
        else:
            factory_method = None
            new = _signature_get_user_defined_method(obj, '__new__')
            init = _signature_get_user_defined_method(obj, '__init__')
            # Now we check if the 'obj' class has an own '__new__' method
            if '__new__' in obj.__dict__:
                factory_method = new
            # or an own '__init__' method
            elif '__init__' in obj.__dict__:
                factory_method = init
            # If not, we take inherited '__new__' or '__init__', if present
            elif new is not None:
                factory_method = new
            elif init is not None:
                factory_method = init

            if factory_method is not None:
                sig = _get_signature_of(factory_method)

        if sig is None:
            # At this point we know, that `obj` is a class, with no user-
            # defined '__init__', '__new__', or class-level '__call__'

            for base in obj.__mro__[:-1]:
                # Since '__text_signature__' is implemented as a
                # descriptor that extracts text signature from the
                # class docstring, if 'obj' is derived from a builtin
                # class, its own '__text_signature__' may be 'None'.
                # Therefore, we go through the MRO (except the last
                # class in there, which is 'object') to find the first
                # class with non-empty text signature.
                try:
                    text_sig = base.__text_signature__
                except AttributeError:
                    pass
                else:
                    if text_sig:
                        # If 'base' class has a __text_signature__ attribute:
                        # return a signature based on it
                        return _signature_fromstr(sigcls, base, text_sig)

            # No '__text_signature__' was found for the 'obj' class.
            # Last option is to check if its '__init__' is
            # object.__init__ or type.__init__.
            if type not in obj.__mro__:
                # We have a class (not metaclass), but no user-defined
                # __init__ or __new__ for it
                if (obj.__init__ is object.__init__ and
                    obj.__new__ is object.__new__):
                    # Return a signature of 'object' builtin.
                    return sigcls.from_callable(object)
                else:
                    raise ValueError(
                        'no signature found for builtin type {!r}'.format(obj))

    elif not isinstance(obj, _NonUserDefinedCallables):
        # An object with __call__
        # We also check that the 'obj' is not an instance of
        # types.WrapperDescriptorType or types.MethodWrapperType to avoid
        # infinite recursion (and even potential segfault)
        call = _signature_get_user_defined_method(type(obj), '__call__')
        if call is not None:
            try:
                sig = _get_signature_of(call)
            except ValueError as ex:
                msg = 'no signature found for {!r}'.format(obj)
                raise ValueError(msg) from ex

    if sig is not None:
        # For classes and objects we skip the first parameter of their
        # __call__, __new__, or __init__ methods
        if skip_bound_arg:
            return _signature_bound_method(sig)
        else:
            return sig

    if isinstance(obj, types.BuiltinFunctionType):
        # Raise a nicer error message for builtins
        msg = 'no signature found for builtin function {!r}'.format(obj)
        raise ValueError(msg)

    raise ValueError('callable {!r} is not supported by signature'.format(obj))


class _ParameterKind(enum.IntEnum):
    POSITIONAL_ONLY = 'positional-only'
    POSITIONAL_OR_KEYWORD = 'positional or keyword'
    VAR_POSITIONAL = 'variadic positional'
    KEYWORD_ONLY = 'keyword-only'
    VAR_KEYWORD = 'variadic keyword'

    def __new__(cls, description):
        value = len(cls.__members__)
        member = int.__new__(cls, value)
        member._value_ = value
        member.description = description
        return member

    def __str__(self):
        return self.name

_POSITIONAL_ONLY         = _ParameterKind.POSITIONAL_ONLY
_POSITIONAL_OR_KEYWORD   = _ParameterKind.POSITIONAL_OR_KEYWORD
_VAR_POSITIONAL          = _ParameterKind.VAR_POSITIONAL
_KEYWORD_ONLY            = _ParameterKind.KEYWORD_ONLY
_VAR_KEYWORD             = _ParameterKind.VAR_KEYWORD


class Parameter:
    """Represents a parameter in a function signature.
    Has the following public attributes:
    * name : str
        The name of the parameter as a string.
    * default : object
        The default value for the parameter if specified.  If the
        parameter has no default value, this attribute is set to
        `Parameter.empty`.
    * annotation
        The annotation for the parameter if specified.  If the
        parameter has no annotation, this attribute is set to
        `Parameter.empty`.
    * kind : str
        Describes how argument values are bound to the parameter.
        Possible values: `Parameter.POSITIONAL_ONLY`,
        `Parameter.POSITIONAL_OR_KEYWORD`, `Parameter.VAR_POSITIONAL`,
        `Parameter.KEYWORD_ONLY`, `Parameter.VAR_KEYWORD`.
    """

    __slots__ = ('_name', '_kind', '_default', '_annotation')

    POSITIONAL_ONLY         = _POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD   = _POSITIONAL_OR_KEYWORD
    VAR_POSITIONAL          = _VAR_POSITIONAL
    KEYWORD_ONLY            = _KEYWORD_ONLY
    VAR_KEYWORD             = _VAR_KEYWORD

    empty = _empty

    def __init__(self, name, kind, *, default=_empty, annotation=_empty):
        try:
            self._kind = _ParameterKind(kind)
        except ValueError:
            raise ValueError(f'value {kind!r} is not a valid Parameter.kind')
        if default is not _empty:
            if self._kind in (_VAR_POSITIONAL, _VAR_KEYWORD):
                msg = '{} parameters cannot have default values'
                msg = msg.format(self._kind.description)
                raise ValueError(msg)
        self._default = default
        self._annotation = annotation

        if name is _empty:
            raise ValueError('name is a required attribute for Parameter')

        if not isinstance(name, str):
            msg = 'name must be a str, not a {}'.format(type(name).__name__)
            raise TypeError(msg)

        if name[0] == '.' and name[1:].isdigit():
            # These are implicit arguments generated by comprehensions. In
            # order to provide a friendlier interface to users, we recast
            # their name as "implicitN" and treat them as positional-only.
            # See issue 19611.
            if self._kind != _POSITIONAL_OR_KEYWORD:
                msg = (
                    'implicit arguments must be passed as '
                    'positional or keyword arguments, not {}'
                )
                msg = msg.format(self._kind.description)
                raise ValueError(msg)
            self._kind = _POSITIONAL_ONLY
            name = 'implicit{}'.format(name[1:])

        # It's possible for C functions to have a positional-only parameter
        # where the name is a keyword, so for compatibility we'll allow it.
        is_keyword = iskeyword(name) and self._kind is not _POSITIONAL_ONLY
        if is_keyword or not name.isidentifier():
            raise ValueError('{!r} is not a valid parameter name'.format(name))

        self._name = name

    def __reduce__(self):
        return (type(self),
                (self._name, self._kind),
                {'_default': self._default,
                 '_annotation': self._annotation})

    def __setstate__(self, state):
        self._default = state['_default']
        self._annotation = state['_annotation']

    @property
    def name(self):
        return self._name

    @property
    def default(self):
        return self._default

    @property
    def annotation(self):
        return self._annotation

    @property
    def kind(self):
        return self._kind

    def replace(self, *, name=_void, kind=_void,
                annotation=_void, default=_void):
        """Creates a customized copy of the Parameter."""

        if name is _void:
            name = self._name

        if kind is _void:
            kind = self._kind

        if annotation is _void:
            annotation = self._annotation

        if default is _void:
            default = self._default

        return type(self)(name, kind, default=default, annotation=annotation)

    def __str__(self):
        kind = self.kind
        formatted = self._name

        # Add annotation and default value
        if self._annotation is not _empty:
            formatted = '{}: {}'.format(formatted,
                                       formatannotation(self._annotation))

        if self._default is not _empty:
            if self._annotation is not _empty:
                formatted = '{} = {}'.format(formatted, repr(self._default))
            else:
                formatted = '{}={}'.format(formatted, repr(self._default))

        if kind == _VAR_POSITIONAL:
            formatted = '*' + formatted
        elif kind == _VAR_KEYWORD:
            formatted = '**' + formatted

        return formatted

    def __repr__(self):
        return '<{} "{}">'.format(self.__class__.__name__, self)

    def __hash__(self):
        return hash((self.name, self.kind, self.annotation, self.default))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Parameter):
            return NotImplemented
        return (self._name == other._name and
                self._kind == other._kind and
                self._default == other._default and
                self._annotation == other._annotation)


class BoundArguments:
    """Result of `Signature.bind` call.  Holds the mapping of arguments
    to the function's parameters.
    Has the following public attributes:
    * arguments : dict
        An ordered mutable mapping of parameters' names to arguments' values.
        Does not contain arguments' default values.
    * signature : Signature
        The Signature object that created this instance.
    * args : tuple
        Tuple of positional arguments values.
    * kwargs : dict
        Dict of keyword arguments values.
    """

    __slots__ = ('arguments', '_signature', '__weakref__')

    def __init__(self, signature, arguments):
        self.arguments = arguments
        self._signature = signature

    @property
    def signature(self):
        return self._signature

    @property
    def args(self):
        args = []
        for param_name, param in self._signature.parameters.items():
            if param.kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
                break

            try:
                arg = self.arguments[param_name]
            except KeyError:
                # We're done here. Other arguments
                # will be mapped in 'BoundArguments.kwargs'
                break
            else:
                if param.kind == _VAR_POSITIONAL:
                    # *args
                    args.extend(arg)
                else:
                    # plain argument
                    args.append(arg)

        return tuple(args)

    @property
    def kwargs(self):
        kwargs = {}
        kwargs_started = False
        for param_name, param in self._signature.parameters.items():
            if not kwargs_started:
                if param.kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
                    kwargs_started = True
                else:
                    if param_name not in self.arguments:
                        kwargs_started = True
                        continue

            if not kwargs_started:
                continue

            try:
                arg = self.arguments[param_name]
            except KeyError:
                pass
            else:
                if param.kind == _VAR_KEYWORD:
                    # **kwargs
                    kwargs.update(arg)
                else:
                    # plain keyword argument
                    kwargs[param_name] = arg

        return kwargs

    def apply_defaults(self):
        """Set default values for missing arguments.
        For variable-positional arguments (*args) the default is an
        empty tuple.
        For variable-keyword arguments (**kwargs) the default is an
        empty dict.
        """
        arguments = self.arguments
        new_arguments = []
        for name, param in self._signature.parameters.items():
            try:
                new_arguments.append((name, arguments[name]))
            except KeyError:
                if param.default is not _empty:
                    val = param.default
                elif param.kind is _VAR_POSITIONAL:
                    val = ()
                elif param.kind is _VAR_KEYWORD:
                    val = {}
                else:
                    # This BoundArguments was likely produced by
                    # Signature.bind_partial().
                    continue
                new_arguments.append((name, val))
        self.arguments = dict(new_arguments)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, BoundArguments):
            return NotImplemented
        return (self.signature == other.signature and
                self.arguments == other.arguments)

    def __setstate__(self, state):
        self._signature = state['_signature']
        self.arguments = state['arguments']

    def __getstate__(self):
        return {'_signature': self._signature, 'arguments': self.arguments}

    def __repr__(self):
        args = []
        for arg, value in self.arguments.items():
            args.append('{}={!r}'.format(arg, value))
        return '<{} ({})>'.format(self.__class__.__name__, ', '.join(args))


class Signature:
    """A Signature object represents the overall signature of a function.
    It stores a Parameter object for each parameter accepted by the
    function, as well as information specific to the function itself.
    A Signature object has the following public attributes and methods:
    * parameters : OrderedDict
        An ordered mapping of parameters' names to the corresponding
        Parameter objects (keyword-only arguments are in the same order
        as listed in `code.co_varnames`).
    * return_annotation : object
        The annotation for the return type of the function if specified.
        If the function has no annotation for its return type, this
        attribute is set to `Signature.empty`.
    * bind(*args, **kwargs) -> BoundArguments
        Creates a mapping from positional and keyword arguments to
        parameters.
    * bind_partial(*args, **kwargs) -> BoundArguments
        Creates a partial mapping from positional and keyword arguments
        to parameters (simulating 'functools.partial' behavior.)
    """

    __slots__ = ('_return_annotation', '_parameters')

    _parameter_cls = Parameter
    _bound_arguments_cls = BoundArguments

    empty = _empty

    def __init__(self, parameters=None, *, return_annotation=_empty,
                 __validate_parameters__=True):
        """Constructs Signature from the given list of Parameter
        objects and 'return_annotation'.  All arguments are optional.
        """

        if parameters is None:
            params = OrderedDict()
        else:
            if __validate_parameters__:
                params = OrderedDict()
                top_kind = _POSITIONAL_ONLY
                kind_defaults = False

                for param in parameters:
                    kind = param.kind
                    name = param.name

                    if kind < top_kind:
                        msg = (
                            'wrong parameter order: {} parameter before {} '
                            'parameter'
                        )
                        msg = msg.format(top_kind.description,
                                         kind.description)
                        raise ValueError(msg)
                    elif kind > top_kind:
                        kind_defaults = False
                        top_kind = kind

                    if kind in (_POSITIONAL_ONLY, _POSITIONAL_OR_KEYWORD):
                        if param.default is _empty:
                            if kind_defaults:
                                # No default for this parameter, but the
                                # previous parameter of the same kind had
                                # a default
                                msg = 'non-default argument follows default ' \
                                      'argument'
                                raise ValueError(msg)
                        else:
                            # There is a default for this parameter.
                            kind_defaults = True

                    if name in params:
                        msg = 'duplicate parameter name: {!r}'.format(name)
                        raise ValueError(msg)

                    params[name] = param
            else:
                params = OrderedDict((param.name, param) for param in parameters)

        self._parameters = types.MappingProxyType(params)
        self._return_annotation = return_annotation

    @classmethod
    def from_callable(cls, obj, *,
                      follow_wrapped=True, globals=None, locals=None, eval_str=False):
        """Constructs Signature for the given callable object."""
        return _signature_from_callable(obj, sigcls=cls,
                                        follow_wrapper_chains=follow_wrapped,
                                        globals=globals, locals=locals, eval_str=eval_str)

    @property
    def parameters(self):
        return self._parameters

    @property
    def return_annotation(self):
        return self._return_annotation

    def replace(self, *, parameters=_void, return_annotation=_void):
        """Creates a customized copy of the Signature.
        Pass 'parameters' and/or 'return_annotation' arguments
        to override them in the new copy.
        """

        if parameters is _void:
            parameters = self.parameters.values()

        if return_annotation is _void:
            return_annotation = self._return_annotation

        return type(self)(parameters,
                          return_annotation=return_annotation)

    def _hash_basis(self):
        params = tuple(param for param in self.parameters.values()
                             if param.kind != _KEYWORD_ONLY)

        kwo_params = {param.name: param for param in self.parameters.values()
                                        if param.kind == _KEYWORD_ONLY}

        return params, kwo_params, self.return_annotation

    def __hash__(self):
        params, kwo_params, return_annotation = self._hash_basis()
        kwo_params = frozenset(kwo_params.values())
        return hash((params, kwo_params, return_annotation))

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Signature):
            return NotImplemented
        return self._hash_basis() == other._hash_basis()

    def _bind(self, args, kwargs, *, partial=False):
        """Private method. Don't use directly."""

        arguments = {}

        parameters = iter(self.parameters.values())
        parameters_ex = ()
        arg_vals = iter(args)

        while True:
            # Let's iterate through the positional arguments and corresponding
            # parameters
            try:
                arg_val = next(arg_vals)
            except StopIteration:
                # No more positional arguments
                try:
                    param = next(parameters)
                except StopIteration:
                    # No more parameters. That's it. Just need to check that
                    # we have no `kwargs` after this while loop
                    break
                else:
                    if param.kind == _VAR_POSITIONAL:
                        # That's OK, just empty *args.  Let's start parsing
                        # kwargs
                        break
                    elif param.name in kwargs:
                        if param.kind == _POSITIONAL_ONLY:
                            msg = '{arg!r} parameter is positional only, ' \
                                  'but was passed as a keyword'
                            msg = msg.format(arg=param.name)
                            raise TypeError(msg) from None
                        parameters_ex = (param,)
                        break
                    elif (param.kind == _VAR_KEYWORD or
                                                param.default is not _empty):
                        # That's fine too - we have a default value for this
                        # parameter.  So, lets start parsing `kwargs`, starting
                        # with the current parameter
                        parameters_ex = (param,)
                        break
                    else:
                        # No default, not VAR_KEYWORD, not VAR_POSITIONAL,
                        # not in `kwargs`
                        if partial:
                            parameters_ex = (param,)
                            break
                        else:
                            msg = 'missing a required argument: {arg!r}'
                            msg = msg.format(arg=param.name)
                            raise TypeError(msg) from None
            else:
                # We have a positional argument to process
                try:
                    param = next(parameters)
                except StopIteration:
                    raise TypeError('too many positional arguments') from None
                else:
                    if param.kind in (_VAR_KEYWORD, _KEYWORD_ONLY):
                        # Looks like we have no parameter for this positional
                        # argument
                        raise TypeError(
                            'too many positional arguments') from None

                    if param.kind == _VAR_POSITIONAL:
                        # We have an '*args'-like argument, let's fill it with
                        # all positional arguments we have left and move on to
                        # the next phase
                        values = [arg_val]
                        values.extend(arg_vals)
                        arguments[param.name] = tuple(values)
                        break

                    if param.name in kwargs and param.kind != _POSITIONAL_ONLY:
                        raise TypeError(
                            'multiple values for argument {arg!r}'.format(
                                arg=param.name)) from None

                    arguments[param.name] = arg_val

        # Now, we iterate through the remaining parameters to process
        # keyword arguments
        kwargs_param = None
        for param in itertools.chain(parameters_ex, parameters):
            if param.kind == _VAR_KEYWORD:
                # Memorize that we have a '**kwargs'-like parameter
                kwargs_param = param
                continue

            if param.kind == _VAR_POSITIONAL:
                # Named arguments don't refer to '*args'-like parameters.
                # We only arrive here if the positional arguments ended
                # before reaching the last parameter before *args.
                continue

            param_name = param.name
            try:
                arg_val = kwargs.pop(param_name)
            except KeyError:
                # We have no value for this parameter.  It's fine though,
                # if it has a default value, or it is an '*args'-like
                # parameter, left alone by the processing of positional
                # arguments.
                if (not partial and param.kind != _VAR_POSITIONAL and
                                                    param.default is _empty):
                    raise TypeError('missing a required argument: {arg!r}'. \
                                    format(arg=param_name)) from None

            else:
                if param.kind == _POSITIONAL_ONLY:
                    # This should never happen in case of a properly built
                    # Signature object (but let's have this check here
                    # to ensure correct behaviour just in case)
                    raise TypeError('{arg!r} parameter is positional only, '
                                    'but was passed as a keyword'. \
                                    format(arg=param.name))

                arguments[param_name] = arg_val

        if kwargs:
            if kwargs_param is not None:
                # Process our '**kwargs'-like parameter
                arguments[kwargs_param.name] = kwargs
            else:
                raise TypeError(
                    'got an unexpected keyword argument {arg!r}'.format(
                        arg=next(iter(kwargs))))

        return self._bound_arguments_cls(self, arguments)

    def bind(self, /, *args, **kwargs):
        """Get a BoundArguments object, that maps the passed `args`
        and `kwargs` to the function's signature.  Raises `TypeError`
        if the passed arguments can not be bound.
        """
        return self._bind(args, kwargs)

    def bind_partial(self, /, *args, **kwargs):
        """Get a BoundArguments object, that partially maps the
        passed `args` and `kwargs` to the function's signature.
        Raises `TypeError` if the passed arguments can not be bound.
        """
        return self._bind(args, kwargs, partial=True)

    def __reduce__(self):
        return (type(self),
                (tuple(self._parameters.values()),),
                {'_return_annotation': self._return_annotation})

    def __setstate__(self, state):
        self._return_annotation = state['_return_annotation']

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self)

    def __str__(self):
        result = []
        render_pos_only_separator = False
        render_kw_only_separator = True
        for param in self.parameters.values():
            formatted = str(param)

            kind = param.kind

            if kind == _POSITIONAL_ONLY:
                render_pos_only_separator = True
            elif render_pos_only_separator:
                # It's not a positional-only parameter, and the flag
                # is set to 'True' (there were pos-only params before.)
                result.append('/')
                render_pos_only_separator = False

            if kind == _VAR_POSITIONAL:
                # OK, we have an '*args'-like parameter, so we won't need
                # a '*' to separate keyword-only arguments
                render_kw_only_separator = False
            elif kind == _KEYWORD_ONLY and render_kw_only_separator:
                # We have a keyword-only parameter to render and we haven't
                # rendered an '*args'-like parameter before, so add a '*'
                # separator to the parameters list ("foo(arg1, *, arg2)" case)
                result.append('*')
                # This condition should be only triggered once, so
                # reset the flag
                render_kw_only_separator = False

            result.append(formatted)

        if render_pos_only_separator:
            # There were only positional-only parameters, hence the
            # flag was not reset to 'False'
            result.append('/')

        rendered = '({})'.format(', '.join(result))

        if self.return_annotation is not _empty:
            anno = formatannotation(self.return_annotation)
            rendered += ' -> {}'.format(anno)

        return rendered


def signature(obj, *, follow_wrapped=True, globals=None, locals=None, eval_str=False):
    """Get a signature object for the passed callable."""
    return Signature.from_callable(obj, follow_wrapped=follow_wrapped,
                                   globals=globals, locals=locals, eval_str=eval_str)

