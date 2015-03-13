# -*- coding: utf-8 -*-
"""Tools for inspecting Python objects.

Uses syntax highlighting for presenting the various information elements.

Similar in spirit to the inspect module, but all calls take a name argument to
reference the name under which an object is being read.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

__all__ = ['Inspector','InspectColors']

# stdlib modules
import inspect
import linecache
import os
from textwrap import dedent
import types
import io as stdlib_io

try:
    from itertools import izip_longest
except ImportError:
    from itertools import zip_longest as izip_longest

# IPython's own
from IPython.core import page
from IPython.lib.pretty import pretty
from IPython.testing.skipdoctest import skip_doctest_py3
from IPython.utils import PyColorize
from IPython.utils import io
from IPython.utils import openpy
from IPython.utils import py3compat
from IPython.utils.dir2 import safe_hasattr
from IPython.utils.path import compress_user
from IPython.utils.text import indent
from IPython.utils.wildcard import list_namespace
from IPython.utils.coloransi import TermColors, ColorScheme, ColorSchemeTable
from IPython.utils.py3compat import cast_unicode, string_types, PY3
from IPython.utils.signatures import signature

# builtin docstrings to ignore
_func_call_docstring = types.FunctionType.__call__.__doc__
_object_init_docstring = object.__init__.__doc__
_builtin_type_docstrings = {
    inspect.getdoc(t) for t in (types.ModuleType, types.MethodType,
                                types.FunctionType, property)
}

_builtin_func_type = type(all)
_builtin_meth_type = type(str.upper)  # Bound methods have the same type as builtin functions
#****************************************************************************
# Builtin color schemes

Colors = TermColors  # just a shorthand

# Build a few color schemes
NoColor = ColorScheme(
    'NoColor',{
    'header' : Colors.NoColor,
    'normal' : Colors.NoColor  # color off (usu. Colors.Normal)
    }  )

LinuxColors = ColorScheme(
    'Linux',{
    'header' : Colors.LightRed,
    'normal' : Colors.Normal  # color off (usu. Colors.Normal)
    } )

LightBGColors = ColorScheme(
    'LightBG',{
    'header' : Colors.Red,
    'normal' : Colors.Normal  # color off (usu. Colors.Normal)
    }  )

# Build table of color schemes (needed by the parser)
InspectColors = ColorSchemeTable([NoColor,LinuxColors,LightBGColors],
                                 'Linux')

#****************************************************************************
# Auxiliary functions and objects

# See the messaging spec for the definition of all these fields.  This list
# effectively defines the order of display
info_fields = ['type_name', 'base_class', 'string_form', 'namespace',
               'length', 'file', 'definition', 'docstring', 'source',
               'init_definition', 'class_docstring', 'init_docstring',
               'call_def', 'call_docstring',
               # These won't be printed but will be used to determine how to
               # format the object
               'ismagic', 'isalias', 'isclass', 'argspec', 'found', 'name'
               ]


def object_info(**kw):
    """Make an object info dict with all fields present."""
    infodict = dict(izip_longest(info_fields, [None]))
    infodict.update(kw)
    return infodict


def get_encoding(obj):
    """Get encoding for python source file defining obj

    Returns None if obj is not defined in a sourcefile.
    """
    ofile = find_file(obj)
    # run contents of file through pager starting at line where the object
    # is defined, as long as the file isn't binary and is actually on the
    # filesystem.
    if ofile is None:
        return None
    elif ofile.endswith(('.so', '.dll', '.pyd')):
        return None
    elif not os.path.isfile(ofile):
        return None
    else:
        # Print only text files, not extension binaries.  Note that
        # getsourcelines returns lineno with 1-offset and page() uses
        # 0-offset, so we must adjust.
        with stdlib_io.open(ofile, 'rb') as buffer:   # Tweaked to use io.open for Python 2
            encoding, lines = openpy.detect_encoding(buffer.readline)
        return encoding

def getdoc(obj):
    """Stable wrapper around inspect.getdoc.

    This can't crash because of attribute problems.

    It also attempts to call a getdoc() method on the given object.  This
    allows objects which provide their docstrings via non-standard mechanisms
    (like Pyro proxies) to still be inspected by ipython's ? system."""
    # Allow objects to offer customized documentation via a getdoc method:
    try:
        ds = obj.getdoc()
    except Exception:
        pass
    else:
        # if we get extra info, we add it to the normal docstring.
        if isinstance(ds, string_types):
            return inspect.cleandoc(ds)
    
    try:
        docstr = inspect.getdoc(obj)
        encoding = get_encoding(obj)
        return py3compat.cast_unicode(docstr, encoding=encoding)
    except Exception:
        # Harden against an inspect failure, which can occur with
        # SWIG-wrapped extensions.
        raise
        return None


def getsource(obj, oname=''):
    """Wrapper around inspect.getsource.

    This can be modified by other projects to provide customized source
    extraction.

    Parameters
    ----------
    obj : object
        an object whose source code we will attempt to extract
    oname : str
        (optional) a name under which the object is known

    Returns
    -------
    src : unicode or None

    """

    if isinstance(obj, property):
        sources = []
        for attrname in ['fget', 'fset', 'fdel']:
            fn = getattr(obj, attrname)
            if fn is not None:
                encoding = get_encoding(fn)
                oname_prefix = ('%s.' % oname) if oname else ''
                sources.append(cast_unicode(
                    ''.join(('# ', oname_prefix, attrname)),
                    encoding=encoding))
                if inspect.isfunction(fn):
                    sources.append(dedent(getsource(fn)))
                else:
                    # Default str/repr only prints function name,
                    # pretty.pretty prints module name too.
                    sources.append(cast_unicode(
                        '%s%s = %s\n' % (
                            oname_prefix, attrname, pretty(fn)),
                        encoding=encoding))
        if sources:
            return '\n'.join(sources)
        else:
            return None

    else:
        # Get source for non-property objects.

        # '__wrapped__' attribute is used by some decorators (e.g. ones defined
        # functools) to provide access to the decorated function.
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__

        try:
            src = inspect.getsource(obj)
        except TypeError:
            # The object itself provided no meaningful source, try looking for
            # its class definition instead.
            if hasattr(obj, '__class__'):
                try:
                    src = inspect.getsource(obj.__class__)
                except TypeError:
                    return None

        encoding = get_encoding(obj)
        return cast_unicode(src, encoding=encoding)


def is_simple_callable(obj):
    """True if obj is a function ()"""
    return (inspect.isfunction(obj) or inspect.ismethod(obj) or \
            isinstance(obj, _builtin_func_type) or isinstance(obj, _builtin_meth_type))


def getargspec(obj):
    """Wrapper around :func:`inspect.getfullargspec` on Python 3, and
    :func:inspect.getargspec` on Python 2.
    
    In addition to functions and methods, this can also handle objects with a
    ``__call__`` attribute.
    """
    if safe_hasattr(obj, '__call__') and not is_simple_callable(obj):
        obj = obj.__call__

    return inspect.getfullargspec(obj) if PY3 else inspect.getargspec(obj)


def format_argspec(argspec):
    """Format argspect, convenience wrapper around inspect's.

    This takes a dict instead of ordered arguments and calls
    inspect.format_argspec with the arguments in the necessary order.
    """
    return inspect.formatargspec(argspec['args'], argspec['varargs'],
                                 argspec['varkw'], argspec['defaults'])


def call_tip(oinfo, format_call=True):
    """Extract call tip data from an oinfo dict.

    Parameters
    ----------
    oinfo : dict

    format_call : bool, optional
      If True, the call line is formatted and returned as a string.  If not, a
      tuple of (name, argspec) is returned.

    Returns
    -------
    call_info : None, str or (str, dict) tuple.
      When format_call is True, the whole call information is formattted as a
      single string.  Otherwise, the object's name and its argspec dict are
      returned.  If no call information is available, None is returned.

    docstring : str or None
      The most relevant docstring for calling purposes is returned, if
      available.  The priority is: call docstring for callable instances, then
      constructor docstring for classes, then main object's docstring otherwise
      (regular functions).
    """
    # Get call definition
    argspec = oinfo.get('argspec')
    if argspec is None:
        call_line = None
    else:
        # Callable objects will have 'self' as their first argument, prune
        # it out if it's there for clarity (since users do *not* pass an
        # extra first argument explicitly).
        try:
            has_self = argspec['args'][0] == 'self'
        except (KeyError, IndexError):
            pass
        else:
            if has_self:
                argspec['args'] = argspec['args'][1:]

        call_line = oinfo['name']+format_argspec(argspec)

    # Now get docstring.
    # The priority is: call docstring, constructor docstring, main one.
    doc = oinfo.get('call_docstring')
    if doc is None:
        doc = oinfo.get('init_docstring')
    if doc is None:
        doc = oinfo.get('docstring','')

    return call_line, doc


def find_file(obj):
    """Find the absolute path to the file where an object was defined.

    This is essentially a robust wrapper around `inspect.getabsfile`.

    Returns None if no file can be found.

    Parameters
    ----------
    obj : any Python object

    Returns
    -------
    fname : str
      The absolute path to the file where the object was defined.
    """
    # get source if obj was decorated with @decorator
    if safe_hasattr(obj, '__wrapped__'):
        obj = obj.__wrapped__

    fname = None
    try:
        fname = inspect.getabsfile(obj)
    except TypeError:
        # For an instance, the file that matters is where its class was
        # declared.
        if hasattr(obj, '__class__'):
            try:
                fname = inspect.getabsfile(obj.__class__)
            except TypeError:
                # Can happen for builtins
                pass
    except:
        pass
    return cast_unicode(fname)


def find_source_lines(obj):
    """Find the line number in a file where an object was defined.

    This is essentially a robust wrapper around `inspect.getsourcelines`.

    Returns None if no file can be found.

    Parameters
    ----------
    obj : any Python object

    Returns
    -------
    lineno : int
      The line number where the object definition starts.
    """
    # get source if obj was decorated with @decorator
    if safe_hasattr(obj, '__wrapped__'):
        obj = obj.__wrapped__
    
    try:
        try:
            lineno = inspect.getsourcelines(obj)[1]
        except TypeError:
            # For instances, try the class object like getsource() does
            if hasattr(obj, '__class__'):
                lineno = inspect.getsourcelines(obj.__class__)[1]
            else:
                lineno = None
    except:
        return None

    return lineno


class Inspector:
    def __init__(self, color_table=InspectColors,
                 code_color_table=PyColorize.ANSICodeColors,
                 scheme='NoColor',
                 str_detail_level=0):
        self.color_table = color_table
        self.parser = PyColorize.Parser(code_color_table,out='str')
        self.format = self.parser.format
        self.str_detail_level = str_detail_level
        self.set_active_scheme(scheme)

    def _getdef(self,obj,oname=''):
        """Return the call signature for any callable object.

        If any exception is generated, None is returned instead and the
        exception is suppressed."""
        try:
            hdef = oname + str(signature(obj))
            return cast_unicode(hdef)
        except:
            return None

    def __head(self,h):
        """Return a header string with proper colors."""
        return '%s%s%s' % (self.color_table.active_colors.header,h,
                           self.color_table.active_colors.normal)

    def set_active_scheme(self, scheme):
        self.color_table.set_active_scheme(scheme)
        self.parser.color_table.set_active_scheme(scheme)

    def noinfo(self, msg, oname):
        """Generic message when no information is found."""
        print('No %s found' % msg, end=' ')
        if oname:
            print('for %s' % oname)
        else:
            print()

    def pdef(self, obj, oname=''):
        """Print the call signature for any callable object.

        If the object is a class, print the constructor information."""

        if not callable(obj):
            print('Object is not callable.')
            return

        header = ''

        if inspect.isclass(obj):
            header = self.__head('Class constructor information:\n')
            obj = obj.__init__
        elif (not py3compat.PY3) and type(obj) is types.InstanceType:
            obj = obj.__call__

        output = self._getdef(obj,oname)
        if output is None:
            self.noinfo('definition header',oname)
        else:
            print(header,self.format(output), end=' ', file=io.stdout)

    # In Python 3, all classes are new-style, so they all have __init__.
    @skip_doctest_py3
    def pdoc(self,obj,oname='',formatter = None):
        """Print the docstring for any object.

        Optional:
        -formatter: a function to run the docstring through for specially
        formatted docstrings.

        Examples
        --------

        In [1]: class NoInit:
           ...:     pass

        In [2]: class NoDoc:
           ...:     def __init__(self):
           ...:         pass

        In [3]: %pdoc NoDoc
        No documentation found for NoDoc

        In [4]: %pdoc NoInit
        No documentation found for NoInit

        In [5]: obj = NoInit()

        In [6]: %pdoc obj
        No documentation found for obj

        In [5]: obj2 = NoDoc()

        In [6]: %pdoc obj2
        No documentation found for obj2
        """

        head = self.__head  # For convenience
        lines = []
        ds = getdoc(obj)
        if formatter:
            ds = formatter(ds)
        if ds:
            lines.append(head("Class docstring:"))
            lines.append(indent(ds))
        if inspect.isclass(obj) and hasattr(obj, '__init__'):
            init_ds = getdoc(obj.__init__)
            if init_ds is not None:
                lines.append(head("Init docstring:"))
                lines.append(indent(init_ds))
        elif hasattr(obj,'__call__'):
            call_ds = getdoc(obj.__call__)
            if call_ds:
                lines.append(head("Call docstring:"))
                lines.append(indent(call_ds))

        if not lines:
            self.noinfo('documentation',oname)
        else:
            page.page('\n'.join(lines))

    def psource(self, obj, oname=''):
        """Print the source code for an object."""

        # Flush the source cache because inspect can return out-of-date source
        linecache.checkcache()
        try:
            src = getsource(obj, oname=oname)
        except Exception:
            src = None

        if src is None:
            self.noinfo('source', oname)
        else:
            page.page(self.format(src))

    def pfile(self, obj, oname=''):
        """Show the whole file where an object was defined."""
        
        lineno = find_source_lines(obj)
        if lineno is None:
            self.noinfo('file', oname)
            return

        ofile = find_file(obj)
        # run contents of file through pager starting at line where the object
        # is defined, as long as the file isn't binary and is actually on the
        # filesystem.
        if ofile.endswith(('.so', '.dll', '.pyd')):
            print('File %r is binary, not printing.' % ofile)
        elif not os.path.isfile(ofile):
            print('File %r does not exist, not printing.' % ofile)
        else:
            # Print only text files, not extension binaries.  Note that
            # getsourcelines returns lineno with 1-offset and page() uses
            # 0-offset, so we must adjust.
            page.page(self.format(openpy.read_py_file(ofile, skip_encoding_cookie=False)), lineno - 1)

    def _format_fields(self, fields, title_width=0):
        """Formats a list of fields for display.

        Parameters
        ----------
        fields : list
          A list of 2-tuples: (field_title, field_content)
        title_width : int
          How many characters to pad titles to. Default to longest title.
        """
        out = []
        header = self.__head
        if title_width == 0:
            title_width = max(len(title) + 2 for title, _ in fields)
        for title, content in fields:
            if len(content.splitlines()) > 1:
                title = header(title + ":") + "\n"
            else:
                title = header((title+":").ljust(title_width))
            out.append(cast_unicode(title) + cast_unicode(content))
        return "\n".join(out)
    
    def _format_info(self, obj, oname='', formatter=None, info=None, detail_level=0):
        """Format an info dict as text"""
        info = self.info(obj, oname=oname, formatter=formatter,
                            info=info, detail_level=detail_level)
        displayfields = []
        def add_fields(fields):
            for title, key in fields:
                field = info[key]
                if field is not None:
                    displayfields.append((title, field.rstrip()))

        if info['isalias']:
            add_fields([('Repr', "string_form")])

        elif info['ismagic']:
            if detail_level > 0 and info['source'] is not None:
                add_fields([("Source", "source")])
            else:
                add_fields([("Docstring", "docstring")])

            add_fields([("File", "file"),
                       ])

        elif info['isclass'] or is_simple_callable(obj):
            # Functions, methods, classes
            add_fields([("Signature", "definition"),
                        ("Init signature", "init_definition"),
                       ])
            if detail_level > 0 and info['source'] is not None:
                add_fields([("Source", "source")])
            else:
                add_fields([("Docstring", "docstring"),
                            ("Init docstring", "init_docstring"),
                           ])

            add_fields([('File', 'file'),
                        ('Type', 'type_name'),
                       ])

        else:
            # General Python objects
            add_fields([("Type", "type_name")])

            # Base class for old-style instances
            if (not py3compat.PY3) and isinstance(obj, types.InstanceType) and info['base_class']:
                displayfields.append(("Base Class", info['base_class'].rstrip()))

            add_fields([("String form", "string_form")])

            # Namespace
            if info['namespace'] != 'Interactive':
                displayfields.append(("Namespace", info['namespace'].rstrip()))

            add_fields([("Length", "length"),
                        ("File", "file"),
                        ("Signature", "definition"),
                       ])

            # Source or docstring, depending on detail level and whether
            # source found.
            if detail_level > 0 and info['source'] is not None:
                displayfields.append(("Source",
                                      self.format(cast_unicode(info['source']))))
            elif info['docstring'] is not None:
                displayfields.append(("Docstring", info["docstring"]))

            add_fields([("Class docstring", "class_docstring"),
                        ("Init docstring", "init_docstring"),
                        ("Call signature", "call_def"),
                        ("Call docstring", "call_docstring")])
        
        if displayfields:
            return self._format_fields(displayfields)
        else:
            return u''
    
    def pinfo(self, obj, oname='', formatter=None, info=None, detail_level=0):
        """Show detailed information about an object.

        Optional arguments:

        - oname: name of the variable pointing to the object.

        - formatter: special formatter for docstrings (see pdoc)

        - info: a structure with some information fields which may have been
          precomputed already.

        - detail_level: if set to 1, more information is given.
        """
        text = self._format_info(obj, oname, formatter, info, detail_level)
        if text:
            page.page(text)
    
    def info(self, obj, oname='', formatter=None, info=None, detail_level=0):
        """Compute a dict with detailed information about an object.

        Optional arguments:

        - oname: name of the variable pointing to the object.

        - formatter: special formatter for docstrings (see pdoc)

        - info: a structure with some information fields which may have been
          precomputed already.

        - detail_level: if set to 1, more information is given.
        """

        obj_type = type(obj)

        if info is None:
            ismagic = 0
            isalias = 0
            ospace = ''
        else:
            ismagic = info.ismagic
            isalias = info.isalias
            ospace = info.namespace

        # Get docstring, special-casing aliases:
        if isalias:
            if not callable(obj):
                try:
                    ds = "Alias to the system command:\n  %s" % obj[1]
                except:
                    ds = "Alias: " + str(obj)
            else:
                ds = "Alias to " + str(obj)
                if obj.__doc__:
                    ds += "\nDocstring:\n" + obj.__doc__
        else:
            ds = getdoc(obj)
            if ds is None:
                ds = '<no docstring>'
        if formatter is not None:
            ds = formatter(ds)

        # store output in a dict, we initialize it here and fill it as we go
        out = dict(name=oname, found=True, isalias=isalias, ismagic=ismagic)

        string_max = 200 # max size of strings to show (snipped if longer)
        shalf = int((string_max -5)/2)

        if ismagic:
            obj_type_name = 'Magic function'
        elif isalias:
            obj_type_name = 'System alias'
        else:
            obj_type_name = obj_type.__name__
        out['type_name'] = obj_type_name

        try:
            bclass = obj.__class__
            out['base_class'] = str(bclass)
        except: pass

        # String form, but snip if too long in ? form (full in ??)
        if detail_level >= self.str_detail_level:
            try:
                ostr = str(obj)
                str_head = 'string_form'
                if not detail_level and len(ostr)>string_max:
                    ostr = ostr[:shalf] + ' <...> ' + ostr[-shalf:]
                    ostr = ("\n" + " " * len(str_head.expandtabs())).\
                            join(q.strip() for q in ostr.split("\n"))
                out[str_head] = ostr
            except:
                pass

        if ospace:
            out['namespace'] = ospace

        # Length (for strings and lists)
        try:
            out['length'] = str(len(obj))
        except: pass

        # Filename where object was defined
        binary_file = False
        fname = find_file(obj)
        if fname is None:
            # if anything goes wrong, we don't want to show source, so it's as
            # if the file was binary
            binary_file = True
        else:
            if fname.endswith(('.so', '.dll', '.pyd')):
                binary_file = True
            elif fname.endswith('<string>'):
                fname = 'Dynamically generated function. No source code available.'
            out['file'] = compress_user(fname)

        # Original source code for a callable, class or property.
        if detail_level:
            # Flush the source cache because inspect can return out-of-date
            # source
            linecache.checkcache()
            try:
                if isinstance(obj, property) or not binary_file:
                    src = getsource(obj, oname)
                    if src is not None:
                        src = src.rstrip()
                    out['source'] = src

            except Exception:
                pass

        # Add docstring only if no source is to be shown (avoid repetitions).
        if ds and out.get('source', None) is None:
            out['docstring'] = ds

        # Constructor docstring for classes
        if inspect.isclass(obj):
            out['isclass'] = True
            # reconstruct the function definition and print it:
            try:
                obj_init =  obj.__init__
            except AttributeError:
                init_def = init_ds = None
            else:
                init_def = self._getdef(obj_init,oname)
                init_ds  = getdoc(obj_init)
                # Skip Python's auto-generated docstrings
                if init_ds == _object_init_docstring:
                    init_ds = None

            if init_def or init_ds:
                if init_def:
                    out['init_definition'] = self.format(init_def)
                if init_ds:
                    out['init_docstring'] = init_ds

        # and class docstring for instances:
        else:
            # reconstruct the function definition and print it:
            defln = self._getdef(obj, oname)
            if defln:
                out['definition'] = self.format(defln)

            # First, check whether the instance docstring is identical to the
            # class one, and print it separately if they don't coincide.  In
            # most cases they will, but it's nice to print all the info for
            # objects which use instance-customized docstrings.
            if ds:
                try:
                    cls = getattr(obj,'__class__')
                except:
                    class_ds = None
                else:
                    class_ds = getdoc(cls)
                # Skip Python's auto-generated docstrings
                if class_ds in _builtin_type_docstrings:
                    class_ds = None
                if class_ds and ds != class_ds:
                    out['class_docstring'] = class_ds

            # Next, try to show constructor docstrings
            try:
                init_ds = getdoc(obj.__init__)
                # Skip Python's auto-generated docstrings
                if init_ds == _object_init_docstring:
                    init_ds = None
            except AttributeError:
                init_ds = None
            if init_ds:
                out['init_docstring'] = init_ds

            # Call form docstring for callable instances
            if safe_hasattr(obj, '__call__') and not is_simple_callable(obj):
                call_def = self._getdef(obj.__call__, oname)
                if call_def:
                    call_def = self.format(call_def)
                    # it may never be the case that call def and definition differ,
                    # but don't include the same signature twice
                    if call_def != out.get('definition'):
                        out['call_def'] = call_def
                call_ds = getdoc(obj.__call__)
                # Skip Python's auto-generated docstrings
                if call_ds == _func_call_docstring:
                    call_ds = None
                if call_ds:
                    out['call_docstring'] = call_ds

        # Compute the object's argspec as a callable.  The key is to decide
        # whether to pull it from the object itself, from its __init__ or
        # from its __call__ method.

        if inspect.isclass(obj):
            # Old-style classes need not have an __init__
            callable_obj = getattr(obj, "__init__", None)
        elif callable(obj):
            callable_obj = obj
        else:
            callable_obj = None

        if callable_obj:
            try:
                argspec = getargspec(callable_obj)
            except (TypeError, AttributeError):
                # For extensions/builtins we can't retrieve the argspec
                pass
            else:
                # named tuples' _asdict() method returns an OrderedDict, but we
                # we want a normal
                out['argspec'] = argspec_dict = dict(argspec._asdict())
                # We called this varkw before argspec became a named tuple.
                # With getfullargspec it's also called varkw.
                if 'varkw' not in argspec_dict:
                    argspec_dict['varkw'] = argspec_dict.pop('keywords')

        return object_info(**out)

    def psearch(self,pattern,ns_table,ns_search=[],
                ignore_case=False,show_all=False):
        """Search namespaces with wildcards for objects.

        Arguments:

        - pattern: string containing shell-like wildcards to use in namespace
          searches and optionally a type specification to narrow the search to
          objects of that type.

        - ns_table: dict of name->namespaces for search.

        Optional arguments:

          - ns_search: list of namespace names to include in search.

          - ignore_case(False): make the search case-insensitive.

          - show_all(False): show all names, including those starting with
            underscores.
        """
        #print 'ps pattern:<%r>' % pattern # dbg

        # defaults
        type_pattern = 'all'
        filter = ''

        cmds = pattern.split()
        len_cmds  =  len(cmds)
        if len_cmds == 1:
            # Only filter pattern given
            filter = cmds[0]
        elif len_cmds == 2:
            # Both filter and type specified
            filter,type_pattern = cmds
        else:
            raise ValueError('invalid argument string for psearch: <%s>' %
                             pattern)

        # filter search namespaces
        for name in ns_search:
            if name not in ns_table:
                raise ValueError('invalid namespace <%s>. Valid names: %s' %
                                 (name,ns_table.keys()))

        #print 'type_pattern:',type_pattern # dbg
        search_result, namespaces_seen = set(), set()
        for ns_name in ns_search:
            ns = ns_table[ns_name]
            # Normally, locals and globals are the same, so we just check one.
            if id(ns) in namespaces_seen:
                continue
            namespaces_seen.add(id(ns))
            tmp_res = list_namespace(ns, type_pattern, filter,
                                    ignore_case=ignore_case, show_all=show_all)
            search_result.update(tmp_res)

        page.page('\n'.join(sorted(search_result)))
