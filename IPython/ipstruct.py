# -*- coding: utf-8 -*-
"""Mimic C structs with lots of extra functionality.

$Id: ipstruct.py 1950 2006-11-28 19:15:35Z vivainio $"""

#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

__all__ = ['Struct']

import types
import pprint

from IPython.genutils import list2dict2

class Struct:
    """Class to mimic C structs but also provide convenient dictionary-like
    functionality.

    Instances can be initialized with a dictionary, a list of key=value pairs
    or both. If both are present, the dictionary must come first.

    Because Python classes provide direct assignment to their members, it's
    easy to overwrite normal methods (S.copy = 1 would destroy access to
    S.copy()). For this reason, all builtin method names are protected and
    can't be assigned to. An attempt to do s.copy=1 or s['copy']=1 will raise
    a KeyError exception. If you really want to, you can bypass this
    protection by directly assigning to __dict__: s.__dict__['copy']=1 will
    still work. Doing this will break functionality, though. As in most of
    Python, namespace protection is weakly enforced, so feel free to shoot
    yourself if you really want to.

    Note that this class uses more memory and is *much* slower than a regular
    dictionary, so be careful in situations where memory or performance are
    critical. But for day to day use it should behave fine. It is particularly
    convenient for storing configuration data in programs.

    +,+=,- and -= are implemented. +/+= do merges (non-destructive updates),
    -/-= remove keys from the original. See the method descripitions.

    This class allows a quick access syntax: both s.key and s['key'] are
    valid.  This syntax has a limitation: each 'key' has to be explicitly
    accessed by its original name. The normal s.key syntax doesn't provide
    access to the keys via variables whose values evaluate to the desired
    keys. An example should clarify this:

    Define a dictionary and initialize both with dict and k=v pairs:
    >>> d={'a':1,'b':2}
    >>> s=Struct(d,hi=10,ho=20)

    The return of __repr__ can be used to create a new instance:
    >>> s
    Struct({'__allownew': True, 'a': 1, 'b': 2, 'hi': 10, 'ho': 20})

    Note: the special '__allownew' key is used for internal purposes.
    
    __str__ (called by print) shows it's not quite a regular dictionary:
    >>> print s
    Struct({'__allownew': True, 'a': 1, 'b': 2, 'hi': 10, 'ho': 20})

    Access by explicitly named key with dot notation:
    >>> s.a
    1

    Or like a dictionary:
    >>> s['a']
    1

    If you want a variable to hold the key value, only dictionary access works:
    >>> key='hi'
    >>> s.key
    Traceback (most recent call last):
      File "<stdin>", line 1, in ?
    AttributeError: Struct instance has no attribute 'key'

    >>> s[key]
    10

    Another limitation of the s.key syntax (and Struct(key=val)
    initialization): keys can't be numbers. But numeric keys can be used and
    accessed using the dictionary syntax. Again, an example:

    This doesn't work (prompt changed to avoid confusing the test system):
    ->> s=Struct(4='hi')
    Traceback (most recent call last):
        ...
    SyntaxError: keyword can't be an expression

    But this does:
    >>> s=Struct()
    >>> s[4]='hi'
    >>> s
    Struct({4: 'hi', '__allownew': True})
    >>> s[4]
    'hi'
    """

    # Attributes to which __setitem__ and __setattr__ will block access.
    # Note: much of this will be moot in Python 2.2 and will be done in a much
    # cleaner way.
    __protected = ('copy dict dictcopy get has_attr has_key items keys '
                   'merge popitem setdefault update values '
                   '__make_dict __dict_invert ').split()

    def __init__(self,dict=None,**kw):
        """Initialize with a dictionary, another Struct, or by giving
        explicitly the list of attributes.

        Both can be used, but the dictionary must come first:
        Struct(dict), Struct(k1=v1,k2=v2) or Struct(dict,k1=v1,k2=v2).
        """
        self.__dict__['__allownew'] = True
        if dict is None:
            dict = {}
        if isinstance(dict,Struct):
            dict = dict.dict()
        elif dict and  type(dict) is not types.DictType:
            raise TypeError,\
                  'Initialize with a dictionary or key=val pairs.'
        dict.update(kw)
        # do the updating by hand to guarantee that we go through the
        # safety-checked __setitem__
        for k,v in dict.items():
            self[k] = v
        

    def __setitem__(self,key,value):
        """Used when struct[key] = val calls are made."""
        if key in Struct.__protected:
            raise KeyError,'Key '+`key`+' is a protected key of class Struct.'
        if not self['__allownew'] and key not in self.__dict__:
            raise KeyError(
            "Can't create unknown attribute %s - Check for typos, or use allow_new_attr to create new attributes!" %
            key)
            
        self.__dict__[key] = value

    def __setattr__(self, key, value):
        """Used when struct.key = val calls are made."""
        self.__setitem__(key,value)

    def __str__(self):
        """Gets called by print."""
        
        return 'Struct('+ pprint.pformat(self.__dict__)+')'

    def __repr__(self):
        """Gets called by repr.
        
        A Struct can be recreated with S_new=eval(repr(S_old))."""
        return self.__str__()

    def __getitem__(self,key):
        """Allows struct[key] access."""
        return self.__dict__[key]

    def __contains__(self,key):
        """Allows use of the 'in' operator."""
        return self.__dict__.has_key(key)

    def __iadd__(self,other):
        """S += S2 is a shorthand for S.merge(S2)."""
        self.merge(other)
        return self

    def __add__(self,other):
        """S + S2 -> New Struct made form S and S.merge(S2)"""
        Sout = self.copy()
        Sout.merge(other)
        return Sout

    def __sub__(self,other):
        """Return S1-S2, where all keys in S2 have been deleted (if present)
        from S1."""
        Sout = self.copy()
        Sout -= other
        return Sout

    def __isub__(self,other):
        """Do in place S = S - S2, meaning all keys in S2 have been deleted
        (if present) from S1."""

        for k in other.keys():
            if self.has_key(k):
                del self.__dict__[k]

    def __make_dict(self,__loc_data__,**kw):
        "Helper function for update and merge. Return a dict from data."

        if __loc_data__ == None:
            dict = {}
        elif type(__loc_data__) is types.DictType:
            dict = __loc_data__
        elif isinstance(__loc_data__,Struct):
            dict = __loc_data__.__dict__
        else:
            raise TypeError, 'Update with a dict, a Struct or key=val pairs.'
        if kw:
            dict.update(kw)
        return dict

    def __dict_invert(self,dict):
        """Helper function for merge. Takes a dictionary whose values are
        lists and returns a dict. with the elements of each list as keys and
        the original keys as values."""

        outdict = {}
        for k,lst in dict.items():
            if type(lst) is types.StringType:
                lst = lst.split()
            for entry in lst:
                outdict[entry] = k
        return outdict

    def clear(self):
        """Clear all attributes."""
        self.__dict__.clear()

    def copy(self):
        """Return a (shallow) copy of a Struct."""
        return Struct(self.__dict__.copy())

    def dict(self):
        """Return the Struct's dictionary."""
        return self.__dict__

    def dictcopy(self):
        """Return a (shallow) copy of the Struct's dictionary."""
        return self.__dict__.copy()

    def popitem(self):
        """S.popitem() -> (k, v), remove and return some (key, value) pair as
        a 2-tuple; but raise KeyError if S is empty."""
        return self.__dict__.popitem()

    def update(self,__loc_data__=None,**kw):
        """Update (merge) with data from another Struct or from a dictionary.
        Optionally, one or more key=value pairs can be given at the end for
        direct update."""

        # The funny name __loc_data__ is to prevent a common variable name which
        # could be a fieled of a Struct to collide with this parameter. The problem
        # would arise if the function is called with a keyword with this same name
        # that a user means to add as a Struct field.
        newdict = Struct.__make_dict(self,__loc_data__,**kw)
        for k,v in newdict.items():
            self[k] = v

    def merge(self,__loc_data__=None,__conflict_solve=None,**kw):
        """S.merge(data,conflict,k=v1,k=v2,...) -> merge data and k=v into S.

        This is similar to update(), but much more flexible.  First, a dict is
        made from data+key=value pairs. When merging this dict with the Struct
        S, the optional dictionary 'conflict' is used to decide what to do.

        If conflict is not given, the default behavior is to preserve any keys
        with their current value (the opposite of the update method's
        behavior).

        conflict is a dictionary of binary functions which will be used to
        solve key conflicts. It must have the following structure:

          conflict == { fn1 : [Skey1,Skey2,...], fn2 : [Skey3], etc }

        Values must be lists or whitespace separated strings which are
        automatically converted to lists of strings by calling string.split().

        Each key of conflict is a function which defines a policy for
        resolving conflicts when merging with the input data. Each fn must be
        a binary function which returns the desired outcome for a key
        conflict. These functions will be called as fn(old,new).

        An example is probably in order. Suppose you are merging the struct S
        with a dict D and the following conflict policy dict:

            S.merge(D,{fn1:['a','b',4], fn2:'key_c key_d'})

        If the key 'a' is found in both S and D, the merge method will call:

            S['a'] = fn1(S['a'],D['a'])

        As a convenience, merge() provides five (the most commonly needed)
        pre-defined policies: preserve, update, add, add_flip and add_s. The
        easiest explanation is their implementation:

          preserve = lambda old,new: old
          update   = lambda old,new: new
          add      = lambda old,new: old + new
          add_flip = lambda old,new: new + old  # note change of order!
          add_s    = lambda old,new: old + ' ' + new  # only works for strings!

        You can use those four words (as strings) as keys in conflict instead
        of defining them as functions, and the merge method will substitute
        the appropriate functions for you. That is, the call

          S.merge(D,{'preserve':'a b c','add':[4,5,'d'],my_function:[6]})

        will automatically substitute the functions preserve and add for the
        names 'preserve' and 'add' before making any function calls.

        For more complicated conflict resolution policies, you still need to
        construct your own functions. """

        data_dict = Struct.__make_dict(self,__loc_data__,**kw)

        # policies for conflict resolution: two argument functions which return
        # the value that will go in the new struct
        preserve = lambda old,new: old
        update   = lambda old,new: new
        add      = lambda old,new: old + new
        add_flip = lambda old,new: new + old  # note change of order!
        add_s    = lambda old,new: old + ' ' + new

        # default policy is to keep current keys when there's a conflict
        conflict_solve = list2dict2(self.keys(),default = preserve)

        # the conflict_solve dictionary is given by the user 'inverted': we
        # need a name-function mapping, it comes as a function -> names
        # dict. Make a local copy (b/c we'll make changes), replace user
        # strings for the three builtin policies and invert it.
        if __conflict_solve:
            inv_conflict_solve_user = __conflict_solve.copy()
            for name, func in [('preserve',preserve), ('update',update),
                               ('add',add), ('add_flip',add_flip),
                               ('add_s',add_s)]:
                if name in inv_conflict_solve_user.keys():
                    inv_conflict_solve_user[func] = inv_conflict_solve_user[name]
                    del inv_conflict_solve_user[name]
            conflict_solve.update(Struct.__dict_invert(self,inv_conflict_solve_user))
        #print 'merge. conflict_solve: '; pprint(conflict_solve) # dbg
        #print '*'*50,'in merger. conflict_solver:';  pprint(conflict_solve)
        for key in data_dict:
            if key not in self:
                self[key] = data_dict[key]
            else:
                self[key] = conflict_solve[key](self[key],data_dict[key])

    def has_key(self,key):
        """Like has_key() dictionary method."""
        return self.__dict__.has_key(key)

    def hasattr(self,key):
        """hasattr function available as a method.

        Implemented like has_key, to make sure that all available keys in the
        internal dictionary of the Struct appear also as attributes (even
        numeric keys)."""
        return self.__dict__.has_key(key)

    def items(self):
        """Return the items in the Struct's dictionary, in the same format
        as a call to {}.items()."""
        return self.__dict__.items()

    def keys(self):
        """Return the keys in the Struct's dictionary, in the same format
        as a call to {}.keys()."""
        return self.__dict__.keys()

    def values(self,keys=None):
        """Return the values in the Struct's dictionary, in the same format
        as a call to {}.values().

        Can be called with an optional argument keys, which must be a list or
        tuple of keys. In this case it returns only the values corresponding
        to those keys (allowing a form of 'slicing' for Structs)."""
        if not keys:
            return self.__dict__.values()
        else:
            ret=[]
            for k in keys:
                ret.append(self[k])
            return ret

    def get(self,attr,val=None):
        """S.get(k[,d]) -> S[k] if k in S, else d.  d defaults to None."""
        try:
            return self[attr]
        except KeyError:
            return val

    def setdefault(self,attr,val=None):
        """S.setdefault(k[,d]) -> S.get(k,d), also set S[k]=d if k not in S"""
        if not self.has_key(attr):
            self[attr] = val
        return self.get(attr,val)
    
    def allow_new_attr(self, allow = True):
        """ Set whether new attributes can be created inside struct
        
        This can be used to catch typos by verifying that the attribute user
        tries to change already exists in this Struct.
        """
        self['__allownew'] = allow
        
        
# end class Struct

