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
import exceptions
import pdb
import pprint
import re
import types

from IPython.genutils import dir2

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

def show_hidden(str,show_all=False):
    """Return true for strings starting with single _ if show_all is true."""
    return show_all or str.startswith("__") or not str.startswith("_")

class NameSpace(object):
    """NameSpace holds the dictionary for a namespace and implements filtering
    on name and types"""
    def __init__(self,obj,name_pattern="*",type_pattern="all",ignore_case=True,
                 show_all=True):
       self.show_all = show_all #Hide names beginning with single _
       self.object = obj
       self.name_pattern = name_pattern
       self.type_pattern = type_pattern
       self.ignore_case = ignore_case
       
       # We should only match EXACT dicts here, so DON'T use isinstance()
       if type(obj) == types.DictType:
           self._ns = obj
       else:
           kv = []
           for key in dir2(obj):
               if isinstance(key, basestring):
                   # This seemingly unnecessary try/except is actually needed
                   # because there is code out there with metaclasses that
                   # create 'write only' attributes, where a getattr() call
                   # will fail even if the attribute appears listed in the
                   # object's dictionary.  Properties can actually do the same
                   # thing.  In particular, Traits use this pattern
                   try:
                       kv.append((key,getattr(obj,key)))
                   except AttributeError:
                       pass
           self._ns = dict(kv)
               
    def get_ns(self):
        """Return name space dictionary with objects matching type and name patterns."""
        return self.filter(self.name_pattern,self.type_pattern)
    ns=property(get_ns)

    def get_ns_names(self):
        """Return list of object names in namespace that match the patterns."""
        return self.ns.keys()
    ns_names=property(get_ns_names,doc="List of objects in name space that "
                      "match the type and name patterns.")
        
    def filter(self,name_pattern,type_pattern):
        """Return dictionary of filtered namespace."""
        def glob_filter(lista,name_pattern,hidehidden,ignore_case):
            """Return list of elements in lista that match pattern."""
            pattern=name_pattern.replace("*",".*").replace("?",".")
            if ignore_case:
                reg=re.compile(pattern+"$",re.I)
            else:
                reg=re.compile(pattern+"$")
            result=[x for x in lista if reg.match(x) and show_hidden(x,hidehidden)]
            return result
        ns=self._ns
        #Filter namespace by the name_pattern
        all=[(x,ns[x]) for x in glob_filter(ns.keys(),name_pattern,
                                            self.show_all,self.ignore_case)]
        #Filter namespace by type_pattern
        all=[(key,obj) for key,obj in all if is_type(obj,type_pattern)]
        all=dict(all)
        return all

    #TODO: Implement dictionary like access to filtered name space?

def list_namespace(namespace,type_pattern,filter,ignore_case=False,show_all=False):
    """Return dictionary of all objects in namespace that matches type_pattern
    and filter."""
    pattern_list=filter.split(".")
    if len(pattern_list)==1:
        ns=NameSpace(namespace,name_pattern=pattern_list[0],type_pattern=type_pattern,
                     ignore_case=ignore_case,show_all=show_all)
        return ns.ns
    else:
        # This is where we can change if all objects should be searched or
        # only modules. Just change the type_pattern to module to search only
        # modules
        ns=NameSpace(namespace,name_pattern=pattern_list[0],type_pattern="all",
                     ignore_case=ignore_case,show_all=show_all)
        res={}
        nsdict=ns.ns
        for name,obj in nsdict.iteritems():
            ns=list_namespace(obj,type_pattern,".".join(pattern_list[1:]),
                              ignore_case=ignore_case,show_all=show_all)
            for inner_name,inner_obj in ns.iteritems():
                res["%s.%s"%(name,inner_name)]=inner_obj
        return res
