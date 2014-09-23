#-----------------------------------------------------------------------------
# Copyright (c) 2014 the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------
#
# Original author: John MacFarlane <jgm@berkeley.edu>
# Copyright: (C) 2013 John MacFarlane
# License: BSD3
# 
# Adapted by Pierre Gerold <gerold@crans.org> for the IPython team
#
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

"""
Functions to aid writing python scripts that process the pandoc
AST serialized as JSON.
"""

import sys
import json

def walk(x, action, format, meta):
    """Walk a tree, applying an action to every object.
    Returns a modified tree.
    """
    if isinstance(x, list):
        array = []
        for item in x:
            if isinstance(item, dict) and 't' in item:
                res = action(item['t'], item['c'], format, meta)
                if res is None:
                    array.append(walk(item, action, format, meta))
                elif isinstance(res, list):
                    for z in res:
                        array.append(walk(z, action, format, meta))
                else:
                    array.append(walk(res, action, format, meta))
            else:
                array.append(walk(item, action, format, meta))
        return array
    elif isinstance(x, dict):
        obj = {}
        for k in x:
            obj[k] = walk(x[k], action, format, meta)
        return obj
    else:
        return x


def elt(eltType, numargs):
    def fun(*args):
        lenargs = len(args)
        if lenargs != numargs:
            raise ValueError(eltType + ' expects ' + str(numargs) + ' arguments, but given ' +
                            str(lenargs))
        if len(args) == 1:
            xs = args[0]
        else:
            xs = args
        return {'t': eltType, 'c': xs}
    return fun

# Constructors for block elements

Plain = elt('Plain',1)
Para = elt('Para',1)
CodeBlock = elt('CodeBlock',2)
RawBlock = elt('RawBlock',2)
BlockQuote = elt('BlockQuote',1)
OrderedList = elt('OrderedList',2)
BulletList = elt('BulletList',1)
DefinitionList = elt('DefinitionList',1)
Header = elt('Header',3)
HorizontalRule = elt('HorizontalRule',0)
Table = elt('Table',5)
Div = elt('Div',2)
Null = elt('Null',0)

# Constructors for inline elements

Str = elt('Str',1)
Emph = elt('Emph',1)
Strong = elt('Strong',1)
Strikeout = elt('Strikeout',1)
Superscript = elt('Superscript',1)
Subscript = elt('Subscript',1)
SmallCaps = elt('SmallCaps',1)
Quoted = elt('Quoted',2)
Cite = elt('Cite',2)
Code = elt('Code',2)
Space = elt('Space',0)
LineBreak = elt('LineBreak',0)
Math = elt('Math',2)
RawInline = elt('RawInline',2)
Link = elt('Link',2)
Image = elt('Image',2)
Note = elt('Note',1)
Span = elt('Span',2)



# The ipython pandoc filter
# this filter should work from any format to any format

def ip_filter(key, value, format, meta):

    # --> latex filter
    # This filter handle the proof, theorem and lemma (and in general can
    # handle any latex environment with slight modification)
    
    if key == 'Div':
        [[ident,classes,kvs], contents] = value
        env_handled = set([u'proof',u'theorem',u'lemma'])
        intersec = env_handled.intersection(classes)
        if intersec:
            env_name = intersec.pop() #one in the intersection
            if format == "latex":
                if ident == "":
                    label = ""
                else:
                    label = '\\label{' + env_name[:3]+':'+ ident + '}'
                return([RawBlock('latex','\\begin{'+ env_name +'}' + label)] +
                       contents + [RawBlock('latex','\\end{'+ env_name +'}')])
