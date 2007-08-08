"""Config file for 'doctest' profile.

This profile modifies the prompts to be the standard Python ones, so that you
can generate easily doctests from an IPython session.

But more importantly, it enables pasting of code with '>>>' prompts and
arbitrary initial whitespace, as is typical of doctests in reST files and
docstrings.  This allows you to easily re-run existing doctests and iteratively
work on them as part of your development workflow.

The exception mode is also set to 'plain' so the generated exceptions are as
similar as possible to the default Python ones, for inclusion in doctests."""

# get various stuff that are there for historical / familiarity reasons
import ipy_legacy

from  IPython import ipapi

from IPython.Extensions import InterpreterPasteInput

def main():    
    ip = ipapi.get()
    o = ip.options

    # Set the prompts similar to the defaults
    o.prompt_in1 = '>>> '
    o.prompt_in2 = '... '
    o.prompt_out = ''

    # No separation between successive inputs
    o.separate_in = ''
    o.separate_out = ''
    # But add a blank line after any output, to help separate doctests from
    # each other.  This is needed by doctest to distinguish each test from the
    # next.
    o.separate_out2 = '\n'

    # Disable pprint, so that outputs are printed as similarly to standard
    # python as possible
    o.pprint = False
    
    # Use plain exceptions, to also resemble normal pyhton.
    o.xmode = 'plain'

main()
