# -*- coding: utf-8 -*-
"""Tools for inspecting Python objects.

Uses syntax highlighting for presenting the various information elements.

Similar in spirit to the inspect module, but all calls take a name argument to
reference the name under which an object is being read.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

__all__ = ['Inspector','InspectColors']

# stdlib modules
import ast
import inspect
from inspect import signature
import linecache
import warnings
import os
from textwrap import dedent
import types
import io as stdlib_io

from typing import Union

# IPython's own
from IPython.core import page
from IPython.lib.pretty import pretty
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils import PyColorize
from IPython.utils import openpy
from IPython.utils.dir2 import safe_hasattr
from IPython.utils.path import compress_user
from IPython.utils.text import indent
from IPython.utils.wildcard import list_namespace
from IPython.utils.wildcard import typestr2type
from IPython.utils.coloransi import TermColors, ColorScheme, ColorSchemeTable
from IPython.utils.py3compat import cast_unicode
from IPython.utils.colorable import Colorable
from IPython.utils.decorators import undoc

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

def pylight(code):
    return highlight(code, PythonLexer(), HtmlFormatter(noclasses=True))

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

InspectColors = PyColorize.ANSICodeColors

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
               'ismagic', 'isalias', 'isclass', 'found', 'name'
               ]


def object_info(**kw):
    """Make an object info dict with all fields present."""
    infodict = {k:None for k in info_fields}
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

def getdoc(obj) -> Union[str,None]:
    """Stable wrapper around inspect.getdoc.

    This can't crash because of attribute problems.

    It also attempts to call a getdoc() method on the given object.  This
    allows objects which provide their docstrings via non-standard mechanisms
    (like Pyro proxies) to still be inspected by ipython's ? system.
    """
    # Allow objects to offer customized documentation via a getdoc method:
    try:
        docstring = obj.getdoc()
    except Exception:
        pass
    else:
        if isinstance(docstring, str):
            return inspect.cleandoc(docstring)
    return inspect.getdoc(obj)


def getsource(obj, oname='') -> Union[str,None]:
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
                sources.append(''.join(('# ', oname_prefix, attrname)))
                if inspect.isfunction(fn):
                    sources.append(dedent(getsource(fn)))
                else:
                    # Default str/repr only prints function name,
                    # pretty.pretty prints module name too.
                    sources.append(
                        '%s%s = %s\n' % (oname_prefix, attrname, pretty(fn))
                    )
        if sources:
            return '\n'.join(sources)
        else:
            return None

    else:
        # Get source for non-property objects.

        obj = _get_wrapped(obj)

        try:
            src = inspect.getsource(obj)
        except TypeError:
            # The object itself provided no meaningful source, try looking for
            # its class definition instead.
            try:
                src = inspect.getsource(obj.__class__)
            except (OSError, TypeError):
                return None
        except OSError:
            return None

        return src


def is_simple_callable(obj):
    """True if obj is a function ()"""
    return (inspect.isfunction(obj) or inspect.ismethod(obj) or \
            isinstance(obj, _builtin_func_type) or isinstance(obj, _builtin_meth_type))

@undoc
def getargspec(obj):
    """Wrapper around :func:`inspect.getfullargspec`

    In addition to functions and methods, this can also handle objects with a
    ``__call__`` attribute.

    DEPRECATED: Deprecated since 7.10. Do not use, will be removed.
    """

    warnings.warn('`getargspec` function is deprecated as of IPython 7.10'
                  'and will be removed in future versions.', DeprecationWarning, stacklevel=2)

    if safe_hasattr(obj, '__call__') and not is_simple_callable(obj):
        obj = obj.__call__

    return inspect.getfullargspec(obj)

@undoc
def format_argspec(argspec):
    """Format argspect, convenience wrapper around inspect's.

    This takes a dict instead of ordered arguments and calls
    inspect.format_argspec with the arguments in the necessary order.

    DEPRECATED (since 7.10): Do not use; will be removed in future versions.
    """
    
    warnings.warn('`format_argspec` function is deprecated as of IPython 7.10'
                  'and will be removed in future versions.', DeprecationWarning, stacklevel=2)


    return inspect.formatargspec(argspec['args'], argspec['varargs'],
                                 argspec['varkw'], argspec['defaults'])

@undoc
def call_tip(oinfo, format_call=True):
    """DEPRECATED since 6.0. Extract call tip data from an oinfo dict."""
    warnings.warn(
        "`call_tip` function is deprecated as of IPython 6.0"
        "and will be removed in future versions.",
        DeprecationWarning,
        stacklevel=2,
    )
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


def _get_wrapped(obj):
    """Try unwrapping an object from its decorators"""
    try:
        return inspect.unwrap(obj)
    except:
        return obj

def find_file(obj) -> str:
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
    obj = _get_wrapped(obj)

    fname = None
    try:
        fname = inspect.getabsfile(obj)
    except TypeError:
        # For an instance, the file that matters is where its class was
        # declared.
        try:
            fname = inspect.getabsfile(obj.__class__)
        except (OSError, TypeError):
            # Can happen for builtins
            pass
    except OSError:
        pass

    return cast_unicode(fname)


def find_source_lines(obj, return_length=False):
    """Find the line number in a file where an object was defined.

    This is essentially a robust wrapper around `inspect.getsourcelines`.

    Returns None if no file can be found.

    Parameters
    ----------
    obj : any Python object
    return_length : whether to return the number of lines in the definition

    Returns
    -------
    lineno : int
        The line number where the object definition starts.
    length : int
        If return_length is True, the number of lines in the definition
    """
    obj = _get_wrapped(obj)

    try:
        lines = inspect.getsourcelines(obj)
    except TypeError:
        # For instances, try the class object like getsource() does
        try:
            lines = inspect.getsourcelines(obj.__class__)
        except (OSError, TypeError):
            return None
    except OSError:
        return None

    if return_length:
        return lines[1], len(lines[0])
    else:
        return lines[1]

class Inspector(Colorable):

    def __init__(self, color_table=InspectColors,
                 code_color_table=PyColorize.ANSICodeColors,
                 scheme=None,
                 str_detail_level=0,
                 parent=None, config=None):
        super(Inspector, self).__init__(parent=parent, config=config)
        self.color_table = color_table
        self.parser = PyColorize.Parser(out='str', parent=self, style=scheme)
        self.format = self.parser.format
        self.str_detail_level = str_detail_level
        self.set_active_scheme(scheme)

    def _getdef(self,obj,oname='') -> Union[str,None]:
        """Return the call signature for any callable object.

        If any exception is generated, None is returned instead and the
        exception is suppressed."""
        try:
            return _render_signature(signature(obj), oname)
        except:
            return None

    def __head(self,h) -> str:
        """Return a header string with proper colors."""
        return '%s%s%s' % (self.color_table.active_colors.header,h,
                           self.color_table.active_colors.normal)

    def set_active_scheme(self, scheme):
        if scheme is not None:
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


        output = self._getdef(obj,oname)
        if output is None:
            self.noinfo('definition header',oname)
        else:
            print(header,self.format(output), end=' ')

    # In Python 3, all classes are new-style, so they all have __init__.
    @skip_doctest
    def pdoc(self, obj, oname='', formatter=None):
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
            ds = formatter(ds).get('plain/text', ds)
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


    def _mime_format(self, text:str, formatter=None) -> dict:
        """Return a mime bundle representation of the input text.

        - if `formatter` is None, the returned mime bundle has
           a ``text/plain`` field, with the input text.
           a ``text/html`` field with a ``<pre>`` tag containing the input text.

        - if ``formatter`` is not None, it must be a callable transforming the
          input text into a mime bundle. Default values for ``text/plain`` and
          ``text/html`` representations are the ones described above.

        Note:

        Formatters returning strings are supported but this behavior is deprecated.

        """
        defaults = {
            'text/plain': text,
            'text/html': '<pre>' + text + '</pre>'
        }

        if formatter is None:
            return defaults
        else:
            formatted = formatter(text)

            if not isinstance(formatted, dict):
                # Handle the deprecated behavior of a formatter returning
                # a string instead of a mime bundle.
                return {
                    'text/plain': formatted,
                    'text/html': '<pre>' + formatted + '</pre>'
                }

            else:
                return dict(defaults, **formatted)


    def format_mime(self, bundle):

        text_plain = bundle['text/plain']

        text = ''
        heads, bodies = list(zip(*text_plain))
        _len = max(len(h) for h in heads)

        for head, body in zip(heads, bodies):
            body = body.strip('\n')
            delim = '\n' if '\n' in body else ' '
            text += self.__head(head+':') + (_len - len(head))*' ' +delim + body +'\n'

        bundle['text/plain'] = text
        return bundle

    def _get_info(
        self, obj, oname="", formatter=None, info=None, detail_level=0, omit_sections=()
    ):
        """Retrieve an info dict and format it.

        Parameters
        ----------
        obj : any
            Object to inspect and return info from
        oname : str (default: ''):
            Name of the variable pointing to `obj`.
        formatter : callable
        info
            already computed information
        detail_level : integer
            Granularity of detail level, if set to 1, give more information.
        omit_sections : container[str]
            Titles or keys to omit from output (can be set, tuple, etc., anything supporting `in`)
        """

        info = self.info(obj, oname=oname, info=info, detail_level=detail_level)

        _mime = {
            'text/plain': [],
            'text/html': '',
        }

        def append_field(bundle, title:str, key:str, formatter=None):
            if title in omit_sections or key in omit_sections:
                return
            field = info[key]
            if field is not None:
                formatted_field = self._mime_format(field, formatter)
                bundle['text/plain'].append((title, formatted_field['text/plain']))
                bundle['text/html'] += '<h1>' + title + '</h1>\n' + formatted_field['text/html'] + '\n'

        def code_formatter(text):
            return {
                'text/plain': self.format(text),
                'text/html': pylight(text)
            }

        if info['isalias']:
            append_field(_mime, 'Repr', 'string_form')

        elif info['ismagic']:
            if detail_level > 0:
                append_field(_mime, 'Source', 'source', code_formatter)
            else:
                append_field(_mime, 'Docstring', 'docstring', formatter)
            append_field(_mime, 'File', 'file')

        elif info['isclass'] or is_simple_callable(obj):
            # Functions, methods, classes
            append_field(_mime, 'Signature', 'definition', code_formatter)
            append_field(_mime, 'Init signature', 'init_definition', code_formatter)
            append_field(_mime, 'Docstring', 'docstring', formatter)
            if detail_level > 0 and info['source']:
                append_field(_mime, 'Source', 'source', code_formatter)
            else:
                append_field(_mime, 'Init docstring', 'init_docstring', formatter)

            append_field(_mime, 'File', 'file')
            append_field(_mime, 'Type', 'type_name')
            append_field(_mime, 'Subclasses', 'subclasses')

        else:
            # General Python objects
            append_field(_mime, 'Signature', 'definition', code_formatter)
            append_field(_mime, 'Call signature', 'call_def', code_formatter)
            append_field(_mime, 'Type', 'type_name')
            append_field(_mime, 'String form', 'string_form')

            # Namespace
            if info['namespace'] != 'Interactive':
                append_field(_mime, 'Namespace', 'namespace')

            append_field(_mime, 'Length', 'length')
            append_field(_mime, 'File', 'file')

            # Source or docstring, depending on detail level and whether
            # source found.
            if detail_level > 0 and info['source']:
                append_field(_mime, 'Source', 'source', code_formatter)
            else:
                append_field(_mime, 'Docstring', 'docstring', formatter)

            append_field(_mime, 'Class docstring', 'class_docstring', formatter)
            append_field(_mime, 'Init docstring', 'init_docstring', formatter)
            append_field(_mime, 'Call docstring', 'call_docstring', formatter)


        return self.format_mime(_mime)

    def pinfo(
        self,
        obj,
        oname="",
        formatter=None,
        info=None,
        detail_level=0,
        enable_html_pager=True,
        omit_sections=(),
    ):
        """Show detailed information about an object.

        Optional arguments:

        - oname: name of the variable pointing to the object.

        - formatter: callable (optional)
              A special formatter for docstrings.

              The formatter is a callable that takes a string as an input
              and returns either a formatted string or a mime type bundle
              in the form of a dictionary.

              Although the support of custom formatter returning a string
              instead of a mime type bundle is deprecated.

        - info: a structure with some information fields which may have been
          precomputed already.

        - detail_level: if set to 1, more information is given.

        - omit_sections: set of section keys and titles to omit
        """
        info = self._get_info(
            obj, oname, formatter, info, detail_level, omit_sections=omit_sections
        )
        if not enable_html_pager:
            del info['text/html']
        page.page(info)

    def _info(self, obj, oname="", info=None, detail_level=0):
        """
        Inspector.info() was likely improperly marked as deprecated
        while only a parameter was deprecated. We "un-deprecate" it.
        """

        warnings.warn(
            "The `Inspector.info()` method has been un-deprecated as of 8.0 "
            "and the `formatter=` keyword removed. `Inspector._info` is now "
            "an alias, and you can just call `.info()` directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.info(obj, oname=oname, info=info, detail_level=detail_level)

    def getstr(self, obj):
        return str(obj)

    def getlen(self, obj):
        return len(obj)

    def info(self, obj, oname="", info=None, detail_level=0) -> dict:
        """Compute a dict with detailed information about an object.

        Parameters
        ----------
        obj : any
            An object to find information about
        oname : str (default: '')
            Name of the variable pointing to `obj`.
        info : (default: None)
            A struct (dict like with attr access) with some information fields
            (ismagic, isalias, namespace) which may have been precomputed already.
        detail_level : int (default:0)
            If set to 1, more information is given.

        Returns
        -------
        An object info dict with known fields from `info_fields`. Keys are
        strings, values are string or None.
        """

        ismagic = getattr(info, "magic", False)
        isalias = getattr(info, "isalias", False)
        ospace = getattr(info, "namespace", None)

        # store output in a dict, we initialize it here and fill it as we go
        out = dict(
            name=oname,
            found=True,
            isalias=isalias,
            ismagic=ismagic,
            isclass=inspect.isclass(obj),
            subclasses=None,
        )

        if ospace:
            out["namespace"] = ospace

        if ismagic:
            out['type_name'] = 'Magic function'
        elif isalias:
            out['type_name'] = 'System alias'
        else:
            out['type_name'] = type(obj).__name__

        try:
            bclass = obj.__class__
            out["base_class"] = self.getstr(bclass)
        except:
            pass

        # Length (for strings and lists)
        try:
            out["length"] = str(self.getlen(obj))
        except Exception:
            pass

        # Filename where object was defined
        binary_file = False
        # TODO: in safeinspect, calling find_file is gated behind this returning true. Perhaps we should have a self.find_file to it can easily be overridden?:
        # inspect.ismodule(obj)
        # or inspect.isclass(obj)
        # or inspect.ismethod(obj)
        # or inspect.isfunction(obj)
        # or inspect.iscode(obj)
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
            try:
                line = find_source_lines(obj, return_length=True)
                if line is not None:
                    out["source_start_line"] = line[0]
                    out["source_end_line"] = line[0] + line[1] - 1
            except:
                pass

        # String form, but snip if too long in ? form (full in ??)
        if detail_level >= self.str_detail_level:
            string_max = 200  # max size of strings to show (snipped if longer)
            shalf = int((string_max - 5) / 2)

            try:
                ostr = self.getstr(obj)
                str_head = "string_form"
                if detail_level == 0 and len(ostr) > string_max:
                    ostr = ostr[:shalf] + " <...> " + ostr[-shalf:]
                    ostr = ("\n" + " " * len(str_head.expandtabs())).join(
                        q.strip() for q in ostr.split("\n")
                    )
                out[str_head] = ostr
            except:
                pass

        # Original source code for a callable, class or property.
        if detail_level > 0:
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

        # Get docstring, special-casing aliases:
        docstring = None
        if isalias:
            # TODO: not sure if we need the self.getstr??
            if not callable(obj):
                try:
                    docstring = "Alias to the system command:\n  " + self.getstr(obj[1])
                except:
                    docstring = "Alias: " + self.getstr(obj)
            else:
                docstring = "Alias to " + self.getstr(obj)
                if obj.__doc__:
                    # TODO: call getdoc instead of manually using __doc__??
                    docstring += "\nDocstring:\n" + obj.__doc__
        else:
            docstring = getdoc(obj)

        if docstring is not None:
            # Add docstring if source does not have it (avoid repetitions).
            if "source" in out:
                if not self._source_contains_docstring(out["source"], docstring):
                    out["docstring"] = docstring
            else:
                out["docstring"] = docstring
        else:
            out["docstring"] = "<no docstring>"

        # Constructor docstring for classes
        if inspect.isclass(obj):
            # get the init signature:
            init_def = self._getdef(obj, oname)

            # get the __init__ docstring and, if still needed, the __init__ signature
            obj_init = getattr(obj, "__init__", None)
            if obj_init:
                init_docstring = getdoc(obj_init)
                # Skip Python's auto-generated docstrings
                if init_docstring == _object_init_docstring:
                    init_docstring = None

                if not init_def:
                    # Get signature from init if top-level sig failed.
                    # Can happen for built-in types (dict, etc.).
                    init_def = self._getdef(obj_init, oname)

            if init_def:
                out['init_definition'] = init_def

            if init_docstring:
                out["init_docstring"] = init_docstring

            names = [sub.__name__ for sub in type.__subclasses__(obj)]
            if len(names) < 10:
                all_names = ', '.join(names)
            else:
                all_names = ', '.join(names[:10]+['...'])
            out['subclasses'] = all_names
        # and class docstring for instances:
        else:
            # reconstruct the function definition and print it:
            definition = self._getdef(obj, oname)
            if definition:
                out["definition"] = definition

            # First, check whether the instance docstring is identical to the
            # class one, and print it separately if they don't coincide.  In
            # most cases they will, but it's nice to print all the info for
            # objects which use instance-customized docstrings.
            if docstring and safe_hasattr(obj, "__class__"):
                class_docstring = getdoc(obj.__class__)
                # Only include the class docstring if is useful and not already included
                if (
                    class_docstring
                    and class_docstring not in _builtin_type_docstrings
                    and class_docstring != docstring
                ):
                    out["class_docstring"] = class_docstring

            # Next, try to show constructor docstrings
            try:
                init_docstring = getdoc(obj.__init__)
                # Skip Python's auto-generated docstrings
                if init_docstring == _object_init_docstring:
                    init_docstring = None
            except AttributeError:
                init_docstring = None
            if init_docstring:
                out["init_docstring"] = init_docstring

            # Call form docstring for callable instances
            if safe_hasattr(obj, '__call__') and not is_simple_callable(obj):
                call_def = self._getdef(obj.__call__, oname)
                if call_def and (call_def != out.get('definition')):
                    # it may never be the case that call def and definition differ,
                    # but don't include the same signature twice
                    out['call_def'] = call_def

                call_docstring = getdoc(obj.__call__)
                # Skip Python's auto-generated docstrings
                if call_docstring != _func_call_docstring:
                    out["call_docstring"] = call_docstring

        return object_info(**out)

    @staticmethod
    def _source_contains_docstring(src, doc):
        """
        Check whether the source *src* contains the docstring *doc*.

        This is a helper function to skip displaying the docstring if the
        source already contains it, avoiding repetition of information.
        """
        try:
            def_node, = ast.parse(dedent(src)).body
            return ast.get_docstring(def_node) == doc
        except Exception:
            # The source can become invalid or even non-existent (because it
            # is re-fetched from the source file) so the above code fail in
            # arbitrary ways.
            return False

    def psearch(self,pattern,ns_table,ns_search=[],
                ignore_case=False,show_all=False, *, list_types=False):
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

          - list_types(False): list all available object types for object matching.
        """
        #print 'ps pattern:<%r>' % pattern # dbg

        # defaults
        type_pattern = 'all'
        filter = ''

        # list all object types
        if list_types:
            page.page('\n'.join(sorted(typestr2type)))
            return

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


# We could have implemented render_signature as a Signature subclass, except that
# we want to take into account the object's name when calculating the line length
def _render_signature(obj_signature, obj_name) -> str:
    """
    This is a copy of inspect.Signature.__str__ with minor formatting improvements

    The only change is to add linebreaks between parameters when the total line length would be very long
    """
    # BEGIN CHANGE
    # We set the self variable so we can just copy the Signature.__str__ code below
    self = obj_signature
    # END CHANGE

    result = []
    render_pos_only_separator = False
    render_kw_only_separator = True
    for param in self.parameters.values():
        formatted = str(param)

        kind = param.kind

        if kind == inspect._POSITIONAL_ONLY:
            render_pos_only_separator = True
        elif render_pos_only_separator:
            # It's not a positional-only parameter, and the flag
            # is set to 'True' (there were pos-only params before.)
            result.append('/')
            render_pos_only_separator = False

        if kind == inspect._VAR_POSITIONAL:
            # OK, we have an '*args'-like parameter, so we won't need
            # a '*' to separate keyword-only arguments
            render_kw_only_separator = False
        elif kind == inspect._KEYWORD_ONLY and render_kw_only_separator:
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

    # BEGIN CHANGE
    # add up name, parameters, braces (2), and commas
    if len(obj_name) + sum(len(r) + 2 for r in result) > 75:
        # This doesn’t fit behind “Signature: ” in an inspect window.
        rendered = '{}(\n{})'.format(obj_name, ''.join(
            '    {},\n'.format(r) for r in result)
        )
    else:
        rendered = '{}({})'.format(obj_name, ', '.join(result))
    # END CHANGE

    if self.return_annotation is not inspect._empty:
        anno = inspect.formatannotation(self.return_annotation)
        rendered += ' -> {}'.format(anno)

    return rendered
