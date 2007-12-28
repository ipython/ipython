"""Doctest-related utilities for IPython.

For most common uses, all you should need to run is::

  from IPython.dtutils import idoctest

See the idoctest docstring below for usage details.
"""

import doctest
import sys

import IPython.ipapi
ip = IPython.ipapi.get()

def rundoctest(text,ns=None,eraise=False):
    """Run a the input source as a doctest, in the caller's namespace.

    :Parameters:
      text : str
        Source to execute.

    :Keywords:
      ns : dict (None)
        Namespace where the code should be executed.  If not given, the
        caller's locals and globals are used.
      eraise : bool (False)
        If true, immediately raise any exceptions instead of reporting them at
        the end.  This allows you to then do interactive debugging via
        IPython's facilities (use %debug after the fact, or with %pdb for
        automatic activation).
    """

    name = 'interactive doctest'
    filename = '<IPython console>'

    if eraise:
        runner = doctest.DebugRunner()
    else:
        runner = doctest.DocTestRunner()
        
    parser = doctest.DocTestParser()
    if ns is None:
        f = sys._getframe(1)
        ns = f.f_globals.copy()
        ns.update(f.f_locals)
        
    test = parser.get_doctest(text,ns,name,filename,0)
    runner.run(test)
    runner.summarize(True)

       
def idoctest(ns=None,eraise=False):
    """Interactively prompt for input and run it as a doctest.

    To finish entering input, enter two blank lines or Ctrl-D (EOF).  If you
    use Ctrl-C, the example is aborted and all input discarded.

    :Keywords:
      ns : dict (None)
        Namespace where the code should be executed.  If not given, the IPython
        interactive namespace is used.
      eraise : bool (False)
        If true, immediately raise any exceptions instead of reporting them at
        the end.  This allows you to then do interactive debugging via
        IPython's facilities (use %debug after the fact, or with %pdb for
        automatic activation).
      end_mark : str ('--')
        String to explicitly indicate the end of input.

    """
    
    inlines = []
    empty_lines = 0  # count consecutive empty lines
    run_test = True

    if ns is None:
        ns = ip.user_ns

    ip.IP.savehist()
    try:
        while True:
            line = raw_input()
            if not line or line.isspace():
                empty_lines += 1
            else:
                empty_lines = 0

            if empty_lines>=2:
                break

            inlines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        print "KeyboardInterrupt - Discarding input."
        run_test = False
    
    ip.IP.reloadhist()

    if run_test:
        # Extra blank line at the end to ensure that the final docstring has a
        # closing newline
        inlines.append('')
        rundoctest('\n'.join(inlines),ns,eraise)


# For debugging of this module itself.
if __name__ == "__main__":
    t = """
    >>> for i in range(10):
    ...     print i,
    ...
    0 1 2 3 4 5 6 7 8 9
    """

    t2 = """
        A simple example::

          >>> for i in range(10):
          ...     print i,
          ...
          0 1 2 3 4 5 6 7 8 9

        Some more details::

          >>> print "hello"
          hello
    """

    t3 = """
        A failing example::

          >>> x=1
          >>> x+1
          3
    """
