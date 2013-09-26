"""Citation handling for LaTeX output."""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


__all__ = ['citation2latex']


def citation2latex(s):
    """Parse citations in Markdown cells.
    
    This looks for HTML tags having a data attribute names `data-cite`
    and replaces it by the call to LaTeX cite command. The tranformation
    looks like this:
    
    `<cite data-cite="granger">(Granger, 2013)</cite>`
    
    Becomes
    
    `\\cite{granger}`
    
    Any HTML tag can be used, which allows the citations to be formatted
    in HTML in any manner.
    """
    import re
    return re.sub("<(?P<tag>[a-z]+) .*?data-cite=['\"]{0,1}(?P<label>[^['\" >]*).*?/(?P=tag)>",
                  '\\cite{\g<label>}',s)
