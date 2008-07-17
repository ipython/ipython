"""Nose Plugin that supports IPython doctests.

Limitations:

- When generating examples for use as doctests, make sure that you have
  pretty-printing OFF.  This can be done either by starting ipython with the
  flag '--nopprint', by setting pprint to 0 in your ipythonrc file, or by
  interactively disabling it with %Pprint.  This is required so that IPython
  output matches that of normal Python, which is used by doctest for internal
  execution.

- Do not rely on specific prompt numbers for results (such as using
  '_34==True', for example).  For IPython tests run via an external process the
  prompt numbers may be different, and IPython tests run as normal python code
  won't even have these special _NN variables set at all.

- IPython functions that produce output as a side-effect of calling a system
  process (e.g. 'ls') can be doc-tested, but they must be handled in an
  external IPython process.  Such doctests must be tagged with:

        # ipdoctest: EXTERNAL

  so that the testing machinery handles them differently.  Since these are run
  via pexpect in an external process, they can't deal with exceptions or other
  fancy featurs of regular doctests.  You must limit such tests to simple
  matching of the output.  For this reason, I recommend you limit these kinds
  of doctests to features that truly require a separate process, and use the
  normal IPython ones (which have all the features of normal doctests) for
  everything else.  See the examples at the bottom of this file for a
  comparison of what can be done with both types.
"""


#-----------------------------------------------------------------------------
# Module imports

# From the standard library
import __builtin__
import commands
import doctest
import inspect
import logging
import os
import re
import sys
import unittest

from inspect import getmodule

# Third-party modules
import nose.core

from nose.plugins import doctests, Plugin
from nose.util import anyp, getpackage, test_address, resolve_name, tolist

# Our own imports
#from extdoctest import ExtensionDoctest, DocTestFinder
#from dttools import DocTestFinder, DocTestCase
#-----------------------------------------------------------------------------
# Module globals and other constants

log = logging.getLogger(__name__)

###########################################################################
# *** HACK ***
# We must start our own ipython object and heavily muck with it so that all the
# modifications IPython makes to system behavior don't send the doctest
# machinery into a fit.  This code should be considered a gross hack, but it
# gets the job done.

def start_ipython():
    """Start a global IPython shell, which we need for IPython-specific syntax.
    """
    import IPython

    def xsys(cmd):
        """Execute a command and print its output.

        This is just a convenience function to replace the IPython system call
        with one that is more doctest-friendly.
        """
        cmd = _ip.IP.var_expand(cmd,depth=1)
        sys.stdout.write(commands.getoutput(cmd))
        sys.stdout.flush()

    # Store certain global objects that IPython modifies
    _displayhook = sys.displayhook
    _excepthook = sys.excepthook
    _main = sys.modules.get('__main__')

    # Start IPython instance
    IPython.Shell.IPShell(['--classic','--noterm_title'])

    # Deactivate the various python system hooks added by ipython for
    # interactive convenience so we don't confuse the doctest system
    sys.modules['__main__'] = _main
    sys.displayhook = _displayhook
    sys.excepthook = _excepthook

    # So that ipython magics and aliases can be doctested (they work by making
    # a call into a global _ip object)
    _ip = IPython.ipapi.get()
    __builtin__._ip = _ip

    # Modify the IPython system call with one that uses getoutput, so that we
    # can capture subcommands and print them to Python's stdout, otherwise the
    # doctest machinery would miss them.
    _ip.system = xsys

# The start call MUST be made here.  I'm not sure yet why it doesn't work if
# it is made later, at plugin initialization time, but in all my tests, that's
# the case.
start_ipython()

# *** END HACK ***
###########################################################################

# Classes and functions

def is_extension_module(filename):
    """Return whether the given filename is an extension module.

    This simply checks that the extension is either .so or .pyd.
    """
    return os.path.splitext(filename)[1].lower() in ('.so','.pyd')


# Modified version of the one in the stdlib, that fixes a python bug (doctests
# not found in extension modules, http://bugs.python.org/issue3158)
class DocTestFinder(doctest.DocTestFinder):

    def _from_module(self, module, object):
        """
        Return true if the given object is defined in the given
        module.
        """
        if module is None:
            #print '_fm C1'  # dbg
            return True
        elif inspect.isfunction(object):
            #print '_fm C2'  # dbg
            return module.__dict__ is object.func_globals
        elif inspect.isbuiltin(object):
            #print '_fm C2-1'  # dbg
            return module.__name__ == object.__module__
        elif inspect.isclass(object):
            #print '_fm C3'  # dbg
            return module.__name__ == object.__module__
        elif inspect.ismethod(object):
            # This one may be a bug in cython that fails to correctly set the
            # __module__ attribute of methods, but since the same error is easy
            # to make by extension code writers, having this safety in place
            # isn't such a bad idea
            #print '_fm C3-1'  # dbg
            return module.__name__ == object.im_class.__module__
        elif inspect.getmodule(object) is not None:
            #print '_fm C4'  # dbg
            #print 'C4 mod',module,'obj',object # dbg
            return module is inspect.getmodule(object)
        elif hasattr(object, '__module__'):
            #print '_fm C5'  # dbg
            return module.__name__ == object.__module__
        elif isinstance(object, property):
            #print '_fm C6'  # dbg
            return True # [XX] no way not be sure.
        else:
            raise ValueError("object must be a class or function")

    def _find(self, tests, obj, name, module, source_lines, globs, seen):
        """
        Find tests for the given object and any contained objects, and
        add them to `tests`.
        """

        doctest.DocTestFinder._find(self,tests, obj, name, module,
                                    source_lines, globs, seen)

        # Below we re-run pieces of the above method with manual modifications,
        # because the original code is buggy and fails to correctly identify
        # doctests in extension modules.

        # Local shorthands
        from inspect import isroutine, isclass, ismodule

        # Look for tests in a module's contained objects.
        if inspect.ismodule(obj) and self._recurse:
            for valname, val in obj.__dict__.items():
                valname1 = '%s.%s' % (name, valname)
                if ( (isroutine(val) or isclass(val))
                     and self._from_module(module, val) ):

                    self._find(tests, val, valname1, module, source_lines,
                               globs, seen)

        # Look for tests in a class's contained objects.
        if inspect.isclass(obj) and self._recurse:
            #print 'RECURSE into class:',obj  # dbg
            for valname, val in obj.__dict__.items():
                #valname1 = '%s.%s' % (name, valname)  # dbg
                #print 'N',name,'VN:',valname,'val:',str(val)[:77] # dbg
                # Special handling for staticmethod/classmethod.
                if isinstance(val, staticmethod):
                    val = getattr(obj, valname)
                if isinstance(val, classmethod):
                    val = getattr(obj, valname).im_func

                # Recurse to methods, properties, and nested classes.
                if ((inspect.isfunction(val) or inspect.isclass(val) or
                     inspect.ismethod(val) or
                      isinstance(val, property)) and
                      self._from_module(module, val)):
                    valname = '%s.%s' % (name, valname)
                    self._find(tests, val, valname, module, source_lines,
                               globs, seen)


class DocTestCase(doctests.DocTestCase):
    """Proxy for DocTestCase: provides an address() method that
    returns the correct address for the doctest case. Otherwise
    acts as a proxy to the test case. To provide hints for address(),
    an obj may also be passed -- this will be used as the test object
    for purposes of determining the test address, if it is provided.
    """

    # doctests loaded via find(obj) omit the module name
    # so we need to override id, __repr__ and shortDescription
    # bonus: this will squash a 2.3 vs 2.4 incompatiblity
    def id(self):
        name = self._dt_test.name
        filename = self._dt_test.filename
        if filename is not None:
            pk = getpackage(filename)
            if pk is not None and not name.startswith(pk):
                name = "%s.%s" % (pk, name)
        return name


# A simple subclassing of the original with a different class name, so we can
# distinguish and treat differently IPython examples from pure python ones.
class IPExample(doctest.Example): pass


class IPExternalExample(doctest.Example):
    """Doctest examples to be run in an external process."""

    def __init__(self, source, want, exc_msg=None, lineno=0, indent=0,
                 options=None):
        # Parent constructor
        doctest.Example.__init__(self,source,want,exc_msg,lineno,indent,options)

        # An EXTRA newline is needed to prevent pexpect hangs
        self.source += '\n'


class IPDocTestParser(doctest.DocTestParser):
    """
    A class used to parse strings containing doctest examples.

    Note: This is a version modified to properly recognize IPython input and
    convert any IPython examples into valid Python ones.
    """
    # This regular expression is used to find doctest examples in a
    # string.  It defines three groups: `source` is the source code
    # (including leading indentation and prompts); `indent` is the
    # indentation of the first (PS1) line of the source code; and
    # `want` is the expected output (including leading indentation).

    # Classic Python prompts or default IPython ones
    _PS1_PY = r'>>>'
    _PS2_PY = r'\.\.\.'

    _PS1_IP = r'In\ \[\d+\]:'
    _PS2_IP = r'\ \ \ \.\.\.+:'

    _RE_TPL = r'''
        # Source consists of a PS1 line followed by zero or more PS2 lines.
        (?P<source>
            (?:^(?P<indent> [ ]*) (?P<ps1> %s) .*)    # PS1 line
            (?:\n           [ ]*  (?P<ps2> %s) .*)*)  # PS2 lines
        \n? # a newline
        # Want consists of any non-blank lines that do not start with PS1.
        (?P<want> (?:(?![ ]*$)    # Not a blank line
                     (?![ ]*%s)   # Not a line starting with PS1
                     (?![ ]*%s)   # Not a line starting with PS2
                     .*$\n?       # But any other line
                  )*)
                  '''

    _EXAMPLE_RE_PY = re.compile( _RE_TPL % (_PS1_PY,_PS2_PY,_PS1_PY,_PS2_PY),
                                 re.MULTILINE | re.VERBOSE)

    _EXAMPLE_RE_IP = re.compile( _RE_TPL % (_PS1_IP,_PS2_IP,_PS1_IP,_PS2_IP),
                                 re.MULTILINE | re.VERBOSE)

    def ip2py(self,source):
        """Convert input IPython source into valid Python."""
        out = []
        newline = out.append
        for lnum,line in enumerate(source.splitlines()):
            #newline(_ip.IPipython.prefilter(line,True))
            newline(_ip.IP.prefilter(line,lnum>0))
        newline('')  # ensure a closing newline, needed by doctest
        return '\n'.join(out)

    def parse(self, string, name='<string>'):
        """
        Divide the given string into examples and intervening text,
        and return them as a list of alternating Examples and strings.
        Line numbers for the Examples are 0-based.  The optional
        argument `name` is a name identifying this string, and is only
        used for error messages.
        """

        #print 'Parse string:\n',string # dbg

        string = string.expandtabs()
        # If all lines begin with the same indentation, then strip it.
        min_indent = self._min_indent(string)
        if min_indent > 0:
            string = '\n'.join([l[min_indent:] for l in string.split('\n')])

        output = []
        charno, lineno = 0, 0

        # Whether to convert the input from ipython to python syntax
        ip2py = False
        # Find all doctest examples in the string.  First, try them as Python
        # examples, then as IPython ones
        terms = list(self._EXAMPLE_RE_PY.finditer(string))
        if terms:
            # Normal Python example
            #print '-'*70  # dbg
            #print 'PyExample, Source:\n',string  # dbg
            #print '-'*70  # dbg
            Example = doctest.Example
        else:
            # It's an ipython example.  Note that IPExamples are run
            # in-process, so their syntax must be turned into valid python.
            # IPExternalExamples are run out-of-process (via pexpect) so they
            # don't need any filtering (a real ipython will be executing them).
            terms = list(self._EXAMPLE_RE_IP.finditer(string))
            if re.search(r'#\s*ipdoctest:\s*EXTERNAL',string):
                #print '-'*70  # dbg
                #print 'IPExternalExample, Source:\n',string  # dbg
                #print '-'*70  # dbg
                Example = IPExternalExample
            else:
                #print '-'*70  # dbg
                #print 'IPExample, Source:\n',string  # dbg
                #print '-'*70  # dbg
                Example = IPExample
                ip2py = True

        for m in terms:
            # Add the pre-example text to `output`.
            output.append(string[charno:m.start()])
            # Update lineno (lines before this example)
            lineno += string.count('\n', charno, m.start())
            # Extract info from the regexp match.
            (source, options, want, exc_msg) = \
                     self._parse_example(m, name, lineno,ip2py)
            if Example is IPExternalExample:
                options[doctest.NORMALIZE_WHITESPACE] = True
                want += '\n'
            # Create an Example, and add it to the list.
            if not self._IS_BLANK_OR_COMMENT(source):
                #print 'Example source:', source # dbg
                output.append(Example(source, want, exc_msg,
                                      lineno=lineno,
                                      indent=min_indent+len(m.group('indent')),
                                      options=options))
            # Update lineno (lines inside this example)
            lineno += string.count('\n', m.start(), m.end())
            # Update charno.
            charno = m.end()
        # Add any remaining post-example text to `output`.
        output.append(string[charno:])

        return output

    def _parse_example(self, m, name, lineno,ip2py=False):
        """
        Given a regular expression match from `_EXAMPLE_RE` (`m`),
        return a pair `(source, want)`, where `source` is the matched
        example's source code (with prompts and indentation stripped);
        and `want` is the example's expected output (with indentation
        stripped).

        `name` is the string's name, and `lineno` is the line number
        where the example starts; both are used for error messages.

        Optional:
        `ip2py`: if true, filter the input via IPython to convert the syntax
        into valid python.
        """

        # Get the example's indentation level.
        indent = len(m.group('indent'))

        # Divide source into lines; check that they're properly
        # indented; and then strip their indentation & prompts.
        source_lines = m.group('source').split('\n')

        # We're using variable-length input prompts
        ps1 = m.group('ps1')
        ps2 = m.group('ps2')
        ps1_len = len(ps1)

        self._check_prompt_blank(source_lines, indent, name, lineno,ps1_len)
        if ps2:
            self._check_prefix(source_lines[1:], ' '*indent + ps2, name, lineno)

        source = '\n'.join([sl[indent+ps1_len+1:] for sl in source_lines])

        if ip2py:
            # Convert source input from IPython into valid Python syntax
            source = self.ip2py(source)

        # Divide want into lines; check that it's properly indented; and
        # then strip the indentation.  Spaces before the last newline should
        # be preserved, so plain rstrip() isn't good enough.
        want = m.group('want')
        want_lines = want.split('\n')
        if len(want_lines) > 1 and re.match(r' *$', want_lines[-1]):
            del want_lines[-1]  # forget final newline & spaces after it
        self._check_prefix(want_lines, ' '*indent, name,
                           lineno + len(source_lines))

        # Remove ipython output prompt that might be present in the first line
        want_lines[0] = re.sub(r'Out\[\d+\]: \s*?\n?','',want_lines[0])

        want = '\n'.join([wl[indent:] for wl in want_lines])

        # If `want` contains a traceback message, then extract it.
        m = self._EXCEPTION_RE.match(want)
        if m:
            exc_msg = m.group('msg')
        else:
            exc_msg = None

        # Extract options from the source.
        options = self._find_options(source, name, lineno)

        return source, options, want, exc_msg

    def _check_prompt_blank(self, lines, indent, name, lineno, ps1_len):
        """
        Given the lines of a source string (including prompts and
        leading indentation), check to make sure that every prompt is
        followed by a space character.  If any line is not followed by
        a space character, then raise ValueError.

        Note: IPython-modified version which takes the input prompt length as a
        parameter, so that prompts of variable length can be dealt with.
        """
        space_idx = indent+ps1_len
        min_len = space_idx+1
        for i, line in enumerate(lines):
            if len(line) >=  min_len and line[space_idx] != ' ':
                raise ValueError('line %r of the docstring for %s '
                                 'lacks blank after %s: %r' %
                                 (lineno+i+1, name,
                                  line[indent:space_idx], line))

SKIP = doctest.register_optionflag('SKIP')


class DocFileCase(doctest.DocFileCase):
    """Overrides to provide filename
    """
    def address(self):
        return (self._dt_test.filename, None, None)


class ExtensionDoctest(doctests.Doctest):
    """Nose Plugin that supports doctests in extension modules.
    """
    name = 'extdoctest'   # call nosetests with --with-extdoctest
    enabled = True

    def options(self, parser, env=os.environ):
        Plugin.options(self, parser, env)

    def configure(self, options, config):
        Plugin.configure(self, options, config)
        self.doctest_tests = options.doctest_tests
        self.extension = tolist(options.doctestExtension)
        self.finder = DocTestFinder()
        self.parser = doctest.DocTestParser()


    def loadTestsFromExtensionModule(self,filename):
        bpath,mod = os.path.split(filename)
        modname = os.path.splitext(mod)[0]
        try:
            sys.path.append(bpath)
            module = __import__(modname)
            tests = list(self.loadTestsFromModule(module))
        finally:
            sys.path.pop()
        return tests

    def loadTestsFromFile(self, filename):
        if is_extension_module(filename):
            for t in self.loadTestsFromExtensionModule(filename):
                yield t
        else:
            ## for t in list(doctests.Doctest.loadTestsFromFile(self,filename)):
            ##     yield t
            pass

        if self.extension and anyp(filename.endswith, self.extension):
            #print 'lTF',filename  # dbg
            name = os.path.basename(filename)
            dh = open(filename)
            try:
                doc = dh.read()
            finally:
                dh.close()
            test = self.parser.get_doctest(
                doc, globs={'__file__': filename}, name=name,
                filename=filename, lineno=0)
            if test.examples:
                #print 'FileCase:',test.examples  # dbg
                yield DocFileCase(test)
            else:
                yield False # no tests to load

    def wantFile(self,filename):
        """Return whether the given filename should be scanned for tests.

        Modified version that accepts extension modules as valid containers for
        doctests.
        """
        #print 'Filename:',filename  # dbg

        # temporarily hardcoded list, will move to driver later
        exclude = ['IPython/external/',
                   'IPython/Extensions/ipy_',
                   'IPython/platutils_win32',
                   'IPython/frontend/cocoa',
                   'IPython_doctest_plugin',
                   'IPython/Gnuplot',
                   'IPython/Extensions/PhysicalQIn']

        for fex in exclude:
            if fex in filename:  # substring
                #print '###>>> SKIP:',filename  # dbg
                return False

        if is_extension_module(filename):
            return True
        else:
            return doctests.Doctest.wantFile(self,filename)

    # NOTE: the method below is a *copy* of the one in the nose doctests
    # plugin, but we have to replicate it here in order to have it resolve the
    # DocTestCase (last line) to our local copy, since the nose plugin doesn't
    # provide a public hook for what TestCase class to use.  The alternative
    # would be to monkeypatch doctest in the stdlib, but that's ugly and
    # brittle, since a change in plugin load order can break it.  So for now,
    # we just paste this in here, inelegant as this may be.

    def loadTestsFromModule(self, module):
        #print 'lTM',module  # dbg

        if not self.matches(module.__name__):
            log.debug("Doctest doesn't want module %s", module)
            return
        tests = self.finder.find(module)
        if not tests:
            return
        tests.sort()
        module_file = module.__file__
        if module_file[-4:] in ('.pyc', '.pyo'):
            module_file = module_file[:-1]
        for test in tests:
            if not test.examples:
                continue
            if not test.filename:
                test.filename = module_file
            yield DocTestCase(test)


class IPythonDoctest(ExtensionDoctest):
    """Nose Plugin that supports doctests in extension modules.
    """
    name = 'ipdoctest'   # call nosetests with --with-ipdoctest
    enabled = True

    def configure(self, options, config):

        Plugin.configure(self, options, config)
        self.doctest_tests = options.doctest_tests
        self.extension = tolist(options.doctestExtension)
        self.parser = IPDocTestParser()
        #self.finder = DocTestFinder(parser=IPDocTestParser())
        self.finder = DocTestFinder(parser=self.parser)
