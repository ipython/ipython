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

from IPython.core import ipapi

from IPython.extensions import InterpreterPasteInput

def main():    
    ip = ipapi.get()
    o = ip.options

    # Set the prompts similar to the defaults
    o.prompt_in1 = '>>> '
    o.prompt_in2 = '... '
    o.prompt_out = ''

    # Add a blank line before each new set of inputs.  This is needed by
    # doctest to distinguish each test from the next.
    o.separate_in = '\n'
    o.separate_out = ''
    o.separate_out2 = ''

    # Disable pprint, so that outputs are printed as similarly to standard
    # python as possible
    o.pprint = False
    
    # Use plain exceptions, to also resemble normal pyhton.
    o.xmode = 'plain'

    # Store the activity flag in the metadata bag from the running shell
    ip.meta.doctest_mode = True

main()
