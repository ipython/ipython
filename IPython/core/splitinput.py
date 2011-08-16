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

# The three parts of the regex are:
#  1) pre:     pre_char *or* initial whitespace 
#  2) ifun:    first word/method (mix of \w and '.')
#  3) the_rest: rest of line (separated from ifun by space if non-empty)
line_split = re.compile(r'^([,;/%?]|!!?|\s*)'
                        r'\s*([\w\.]+)'
                        r'(\s+.*$|$)')

# r'[\w\.]+'
# r'\s*=\s*%.*'

def split_user_input(line, pattern=None):
    """Split user input into pre-char/whitespace, function part and rest.

    This is currently handles lines with '=' in them in a very inconsistent
    manner.
    """
    # We need to ensure that the rest of this routine deals only with unicode
    if type(line)==str:
        codec = sys.stdin.encoding
        if codec is None:
            codec = 'utf-8'
        line = line.decode(codec)
        
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
    else:
        pre,ifun,the_rest = match.groups()

    # ifun has to be a valid python identifier, so it better encode into
    # ascii.  We do still make it a unicode string so that we consistently
    # return unicode, but it will be one that is guaranteed to be pure ascii
    try:
        ifun = unicode(ifun.encode('ascii'))
    except UnicodeEncodeError:
        the_rest = ifun + u' ' + the_rest
        ifun = u''

    #print 'line:<%s>' % line # dbg
    #print 'pre <%s> ifun <%s> rest <%s>' % (pre,ifun.strip(),the_rest) # dbg
    return pre, ifun.strip(), the_rest.lstrip()
