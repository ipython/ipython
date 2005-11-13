# -*- coding: utf-8 -*-
"""Support for wildcard pattern matching in object inspection.

$Id: OInspect.py 608 2005-07-06 17:52:32Z fperez $
"""

#*****************************************************************************
#       Copyright (C) 2005 Jörgen Stenarson <jorgen.stenarson@bostream.nu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = "Jörgen Stenarson <jorgen.stenarson@bostream.nu>"
__license__ = Release.license

import __builtin__
import types
import re
import pprint
import exceptions
import pdb
import IPython.genutils as genutils

def create_typestr2type_dicts(dont_include_in_type2type2str=["lambda"]):
    """Return dictionaries mapping lower case typename to type objects, from
    the types package, and vice versa."""
    typenamelist=[]
    for tname in dir(types):
        if tname[-4:]=="Type":
            typenamelist.append(tname)
    typestr2type={}
    type2typestr={}
    for tname in typenamelist:
        name=tname[:-4].lower()
        obj=getattr(types,tname)
        typestr2type[name]=getattr(types,tname)
        if name in dont_include_in_type2type2str:
            type2typestr[obj]=name
    return typestr2type,type2typestr

typestr2type,type2typestr=create_typestr2type_dicts()

def is_type(obj,typestr_or_type):
    """is_type(obj,typestr_or_type) verifies if obj is of a certain type or
    group of types takes strings as parameters of the for 'tuple'<->TupleType
    'all' matches all types.  TODO: Should be extended for choosing more than
    one type
    """
    if typestr_or_type=="all":
        return True
    if type(typestr_or_type)==types.TypeType:
        test_type=typestr_or_type
    else:
        test_type=typestr2type.get(typestr_or_type,False)
    if test_type:
        return isinstance(obj,test_type)
    else:
        return False

def show_hidden(str,showhidden=False):
    """Return true for strings starting with single _ if showhidden is true."""
    return showhidden or str.startswith("__") or not str.startswith("_")


class NameSpace(object):
    """NameSpace holds the dictionary for a namespace and implements filtering
    on name and types"""
    def __init__(self,obj,namepattern="*",typepattern="all",ignorecase=True,
                 showhidden=True):
       self.showhidden = showhidden #Hide names beginning with single _
       self.object = obj
       self.namepattern = namepattern
       self.typepattern = typepattern
       self.ignorecase = ignorecase
       
       # We should only match EXACT dicts here, so DON'T use isinstance()
       if type(obj) == types.DictType:
           self._ns = obj
       else:
           self._ns = dict([(key,getattr(obj,key)) for key in dir(obj)
                            if isinstance(key, basestring)])
               
    def get_ns(self):
        """Return name space dictionary with objects matching type and name patterns."""
        return self.filter(self.namepattern,self.typepattern)
    ns=property(get_ns)

    def get_ns_names(self):
        """Return list of object names in namespace that match the patterns."""
        return self.ns.keys()
    ns_names=property(get_ns_names,doc="List of objects in name space that "
                      "match the type and name patterns.")
        
    def filter(self,namepattern,typepattern):
        """Return dictionary of filtered namespace."""
        def glob_filter(lista,namepattern,hidehidden,ignorecase):
            """Return list of elements in lista that match pattern."""
            pattern=namepattern.replace("*",".*")
            if ignorecase:
                reg=re.compile(pattern+"$",re.I)
            else:
                reg=re.compile(pattern+"$")
            result=[x for x in lista if reg.match(x) and show_hidden(x,hidehidden)]
            return result
        ns=self._ns
        #Filter namespace by the namepattern
        all=[(x,ns[x]) for x in glob_filter(ns.keys(),namepattern,
                                            self.showhidden,self.ignorecase)]
        #Filter namespace by typepattern
        all=[(key,obj) for key,obj in all if is_type(obj,typepattern)]
        all=dict(all)
        return all

    #TODO: Implement dictionary like access to filtered name space?

def list_namespace(namespace,typepattern,filter,ignorecase=False,showhidden=False):
    """Return dictionary of all objects in namespace that matches typepattern
    and filter."""
    patternlist=filter.split(".")
    if len(patternlist)==1:
        ns=NameSpace(namespace,namepattern=patternlist[0],typepattern=typepattern,
                     ignorecase=ignorecase,showhidden=showhidden)
        return ns.ns
    if len(patternlist)>1:
        #This is where we can change if all objects should be searched or only moduleas
        #Just change the typepattern to module to search only modules
        ns=NameSpace(namespace,
                     namepattern=patternlist[0],
                     typepattern="all",ignorecase=ignorecase,showhidden=showhidden)
        res={}
        nsdict=ns.ns
        for name,obj in nsdict.iteritems():
            ns=list_namespace(obj,typepattern,".".join(patternlist[1:]),
                              ignorecase=ignorecase,showhidden=showhidden)
            for inner_name,inner_obj in ns.iteritems():
                res["%s.%s"%(name,inner_name)]=inner_obj
        return res

def choose_namespaces(shell,cmds):
    """Returns a list of namespaces modified by arguments."""
    nslist=genutils.mkdict(user=shell.user_ns,internal=shell.internal_ns,
               builtin=__builtin__.__dict__,alias=shell.alias_table)
    default_list=["user","builtin"]  # Should this list be a user option??
    for cmd in cmds:
        if cmd[0]=="-":  #remove from defaultlist
            if cmd[1:] in default_list:
                default_list.remove(cmd[1:])
        elif cmd[0]=="+":
            if cmd[1:] not in default_list and cmd[1:]in nslist:
                default_list.append(cmd[1:])
        else:
            if cmd in nslist:
                default_list.append(cmd[1:])
    return [nslist[x] for x in default_list]
