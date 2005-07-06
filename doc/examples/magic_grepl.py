"""This function implements a simple grep-like function in pure python.

You can enable it by copying it to your ~/.ipython directory and putting

execfile = magic_grepl.py

in your ipythonrc file.

Code contributed by Gever Tulley <gever@helium.com>, minor changes applied.
"""

import glob
import re
import os

def magic_grepl(self, parameter_s=''):
    """Search for a pattern in a list of files.

    It prints the names of the files containing the pattern. Similar to 'grep
    -l' in Unix-like environments.

    Usage: @grepl pattern [files]

    - pattern:  any regular expression pattern which re.compile() will accept.
    - files: list of files to scan.  It can contain standard unix wildcards.
    """

    # argument processing
    params = parameter_s.split()
    if len(params) > 1:
        target = params[0]    # first one is the target
        file_patterns = params[1:]    # all the rest are filenames or patterns

        # build the regular expression
        expr = re.compile(target)

        for pattern in file_patterns:
            flist = [f for f in glob.glob(pattern) if os.path.isfile(f)]
            for filename in flist:
                # open and read the whole file
                f = open(filename,'r')
                data = f.read()
                f.close()

                # see if pattern occurs in the file
                if expr.search(data):
                    print filename
    else:
        # no parameters given
        print("Usage: @grepl pattern [files]");

# Add the new magic function to the class dict:
from IPython.iplib import InteractiveShell
InteractiveShell.magic_grepl = magic_grepl

# And remove the global name to keep global namespace clean.  Don't worry, the
# copy bound to IPython stays, we're just removing the global name.
del magic_grepl

#********************** End of file <magic_grepl.py> ***********************
