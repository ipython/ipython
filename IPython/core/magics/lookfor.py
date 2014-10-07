# -*- coding: utf-8 -*-
"""
%lookfor command for searching docstrings.

"""
from __future__ import print_function
#-----------------------------------------------------------------------------
#  Copyright (c) 2012, The IPython Development Team.
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Stdlib
import re, os, sys, inspect, pkgutil, pydoc, textwrap

# Our own
from IPython.core.error import UsageError
from IPython.core.magic import Magics, magics_class, line_magic
from IPython.testing.skipdoctest import skip_doctest
from IPython.utils.traitlets import Bool
from IPython.utils.py3compat import string_types

#------------------------------------------------------------------------------
# Lookfor functionality
#------------------------------------------------------------------------------

# Cache for lookfor: {id(module): {name: (docstring, kind, index), ...}...}
# where kind: "func", "class", "module", "object"
# and index: index in breadth-first namespace traversal
_lookfor_caches = {}

# regexp whose match indicates that the string may contain a function signature
_function_signature_re = re.compile(r"[a-z_]+\(.*[,=].*\)", re.I)


@magics_class
class LookforMagics(Magics):
    """ Search functionality in modules docstrings.

    Provides the %lookfor magic."""

    def __init__(self, shell):
        super(LookforMagics, self).__init__(shell=shell)
        self.shell.configurables.append(self)

    @skip_doctest
    @line_magic
    def lookfor(self, parameter_s=''):
        """
        Search for objects whose documentation contains all given words.
        Shows a summary of matching objects, sorted roughly by relevance.

        %lookfor [-r] what module

        what : str
            String containing words to look for

        module : str
            Modules whose docstrings to go through

        Options:

          -r
            Re-generate the docstring cache

        """
        opts,args = self.parse_options(parameter_s,'r',mode='list')
        if len(args) < 2:
            raise UsageError(
                "%macro insufficient args; usage '%lookfor what module'")

        regen = 'r' in opts

        what = args[0]
        mods = args[1:]

        return self.lookfor_f(what, modules=mods, regenerate=regen)


    def lookfor_f(self, what, modules=None, import_modules=True, regenerate=False):
        """
        Search for objects whose documentation contains all given words.
        Shows a summary of matching objects, sorted roughly by relevance.

        Parameters
        ----------
        what : str
            String containing words to look for.

        module : str, module
            Module whose docstrings to go through.
        import_modules : bool
            Whether to import sub-modules in packages.
            Will import only modules in __all__
        regenerate: bool
            Re-generate the docstring cache

        """
        # Cache
        cache = {}

        for module in modules:
            try:
                c = self._lookfor_generate_cache(module, import_modules, regenerate)
                cache.update(c)
            except ImportError:
                pass

        # Search
        # XXX: maybe using a real stemming search engine would be better?
        found = []
        whats = str(what).lower().split()
        if not whats: return

        for name, (docstring, kind, index) in cache.items():
            if kind in ('module', 'object'):
                # don't show modules or objects
                continue
            ok = True
            doc = docstring.lower()
            for w in whats:
                if w not in doc:
                    ok = False
                    break
            if ok:
                found.append(name)

        # Relevance sort
        # XXX: this is full Harrison-Stetson heuristics now,
        # XXX: it probably could be improved

        kind_relevance = {'func': 1000, 'class': 1000,
                          'module': -1000, 'object': -1000}

        def relevance(name, docstr, kind, index):
            r = 0
            # do the keywords occur within the start of the docstring?
            first_doc = "\n".join(docstr.lower().strip().split("\n")[:3])
            r += sum([200 for w in whats if w in first_doc])
            # do the keywords occur in the function name?
            r += sum([30 for w in whats if w in name])
            # is the full name long?
            r += -len(name) * 5
            # is the object of bad type?
            r += kind_relevance.get(kind, -1000)
            # is the object deep in namespace hierarchy?
            r += -name.count('.') * 10
            r += max(-index / 100, -100)
            return r

        def relevance_sort(a, b):
            dr = relevance(b, *cache[b]) - relevance(a, *cache[a])
            if dr != 0: return dr
            else: return (a > b) - (a < b)

        # sort found according to relevance
        for i in range(len(found)):
            for j in range(i):
                if (relevance_sort(found[j],found[j+1]) > 0):
                    tmp = found[j]
                    found[j] = found[j+1]
                    found[j+1] = tmp

        # Pretty-print
        s = "Search results for '%s'" % (' '.join(whats))
        help_text = [s, "-"*len(s)]
        for name in found:
            doc, kind, ix = cache[name]

            doclines = [line.strip() for line in doc.strip().split("\n")
                        if line.strip()]

            # find a suitable short description
            try:
                first_doc = doclines[0].strip()
                if _function_signature_re.search(first_doc):
                    first_doc = doclines[1].strip()
            except IndexError:
                first_doc = ""
            help_text.append("%s\n    %s" % (name, first_doc))

        # Output
        if len(help_text) > 10:
            pager = pydoc.getpager()
            pager("\n".join(help_text))
        else:
            print("\n".join(help_text))

    def _lookfor_generate_cache(self, module, import_modules, regenerate):
        """
        Generate docstring cache for given module.

        Parameters
        ----------
        module : str, None, module
            Module for which to generate docstring cache
        import_modules : bool
            Whether to import sub-modules in packages.
            Will import only modules in __all__
        regenerate: bool
            Re-generate the docstring cache

        Returns
        -------
        cache : dict {obj_full_name: (docstring, kind, index), ...}
            Docstring cache for the module, either cached one (regenerate=False)
            or newly generated.

        """
        global _lookfor_caches

        if module is None:
            module = 'numpy'

        if isinstance(module, basestring):
            module = __import__(module)

        if id(module) in _lookfor_caches and not regenerate:
            return _lookfor_caches[id(module)]

        # walk items and collect docstrings
        cache = {}
        _lookfor_caches[id(module)] = cache
        seen = {}
        index = 0
        stack = [(module.__name__, module)]
        while stack:
            name, item = stack.pop(0)
            if id(item) in seen: continue
            seen[id(item)] = True

            index += 1
            kind = 'object'

            if inspect.ismodule(item):
                kind = 'module'
                try:
                    _all = item.__all__
                except AttributeError:
                    _all = None
                # import sub-packages
                if import_modules and hasattr(item, '__path__'):
                    for m in pkgutil.iter_modules(item.__path__):
                        if _all is not None and m[1] not in _all:
                            continue
                        try:
                            __import__("%s.%s" % (name, m[1]))
                        except ImportError:
                            continue
                for n, v in inspect.getmembers(item):
                    if _all is not None and n not in _all:
                        continue
                    stack.append(("%s.%s" % (name, n), v))
            elif inspect.isclass(item):
                kind = 'class'
                for n, v in inspect.getmembers(item):
                    stack.append(("%s.%s" % (name, n), v))
            elif callable(item):
                kind = 'func'

            doc = inspect.getdoc(item)
            if doc is not None:
                cache[name] = (doc, kind, index)

        return cache

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(LookforMagics)
