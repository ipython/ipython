# encoding: utf-8
"""
Simple utility for splitting user input.

Authors:

* Brian Granger
* Fernando Perez
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import re
import sys

from IPython.utils import py3compat

#-----------------------------------------------------------------------------
# Main function
#-----------------------------------------------------------------------------


# RegExp for splitting line contents into pre-char//first word-method//rest.
# For clarity, each group in on one line.

# WARNING: update the regexp if the escapes in interactiveshell are changed, as they
# are hardwired in.

# Although it's not solely driven by the regex, note that:
# ,;/% only trigger if they are the first character on the line
# ! and !! trigger if they are first char(s) *or* follow an indent 
# ? triggers as first or last char.

# The four parts of the regex are:
#  1) pre:     initial whitespace
#  2) esc:     escape character
#  3) ifun:    first word/method (mix of \w and '.')
#  4) the_rest: rest of line (separated from ifun by space if non-empty)
line_split = re.compile(r'^(\s*)'
                        r'([,;/%?]|!!?)?'
                        r'\s*([\w\.]+)'
                        r'(.*$|$)')

# r'[\w\.]+'
# r'\s*=\s*%.*'

def split_user_input(line, pattern=None):
    """Split user input into pre-char/whitespace, function part and rest.

    This is currently handles lines with '=' in them in a very inconsistent
    manner.
    """
    # We need to ensure that the rest of this routine deals only with unicode
    line = py3compat.cast_unicode(line, sys.stdin.encoding or 'utf-8')
        
    if pattern is None:
        pattern = line_split
    match = pattern.match(line)
    if not match:
        # print "match failed for line '%s'" % line
        try:
            ifun, the_rest = line.split(None,1)
        except ValueError:
            # print "split failed for line '%s'" % line
            ifun, the_rest = line, u''
        pre = re.match('^(\s*)(.*)',line).groups()[0]
        esc = ""
    else:
        pre, esc, ifun, the_rest = match.groups()
    
    if not py3compat.isidentifier(ifun, dotted=True):
        the_rest = ifun + u' ' + the_rest
        ifun = u''

    #print 'line:<%s>' % line # dbg
    #print 'pre <%s> ifun <%s> rest <%s>' % (pre,ifun.strip(),the_rest) # dbg
    return pre, esc, ifun.strip(), the_rest.lstrip()
