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


__all__ = ['parse_citation']


def parse_citation(s):
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
    try:
        from lxml import html
    except ImportError:
        return s

    tree = html.fragment_fromstring(s, create_parent='div')
    _process_node_cite(tree)
    s = html.tostring(tree)
    if s.endswith('</div>'):
        s = s[:-6]
    if s.startswith('<div>'):
        s = s[5:]
    return s


def _process_node_cite(node):
    """Do the citation replacement as we walk the lxml tree."""
    
    def _get(o, name):
        value = getattr(o, name)
        return '' if value is None else value
    
    if 'data-cite' in node.attrib:
        cite = '\cite{%(ref)s}' % {'ref': node.attrib['data-cite']}
        prev = node.getprevious()
        if prev is not None:
            prev.tail = _get(prev, 'tail') + cite + _get(node, 'tail')
        else:
            parent = node.getparent()
            if parent is not None:
                parent.text = _get(parent, 'text') + cite + _get(node, 'tail')
        try:
            node.getparent().remove(node)
        except AttributeError:
            pass
    else:
        for child in node:
            _process_node_cite(child)
