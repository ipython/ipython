# Online Python Tutor
# https://github.com/pgbovine/OnlinePythonTutor/
#
# Copyright (C) 2010-2012 Philip J. Guo (philip@pgbovine.net)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# Thanks to John DeNero for making the encoder work on both Python 2 and 3


# Given an arbitrary piece of Python data, encode it in such a manner
# that it can be later encoded into JSON.
#   http://json.org/
#
# We use this function to encode run-time traces of data structures
# to send to the front-end.
#
# Format:
#   Primitives:
#   * None, int, long, float, str, bool - unchanged
#     (json.dumps encodes these fine verbatim)
#
#   Compound objects:
#   * list     - ['LIST', elt1, elt2, elt3, ..., eltN]
#   * tuple    - ['TUPLE', elt1, elt2, elt3, ..., eltN]
#   * set      - ['SET', elt1, elt2, elt3, ..., eltN]
#   * dict     - ['DICT', [key1, value1], [key2, value2], ..., [keyN, valueN]]
#   * instance - ['INSTANCE', class name, [attr1, value1], [attr2, value2], ..., [attrN, valueN]]
#   * class    - ['CLASS', class name, [list of superclass names], [attr1, value1], [attr2, value2], ..., [attrN, valueN]]
#   * function - ['FUNCTION', function name, parent frame ID (for nested functions)]
#   * module   - ['module', module name]
#   * other    - [<type name>, string representation of object]
#   * compound object reference - ['REF', target object's unique_id]
#
# the unique_id is derived from id(), which allows us to capture aliasing


# number of significant digits for floats
FLOAT_PRECISION = 4


import re, types
import sys
typeRE = re.compile("<type '(.*)'>")
classRE = re.compile("<class '(.*)'>")

import inspect

is_python3 = (sys.version_info[0] == 3)
if is_python3:
  long = None # Avoid NameError when evaluating "long"


def is_class(dat):
  """Return whether dat is a class."""
  if is_python3:
    return isinstance(dat, type)
  else:
    return type(dat) in (types.ClassType, types.TypeType)


def is_instance(dat):
  """Return whether dat is an instance of a class."""
  if is_python3:
    return isinstance(type(dat), type) and not isinstance(dat, type)
  else:
    # ugh, classRE match is a bit of a hack :(
    return type(dat) == types.InstanceType or classRE.match(str(type(dat)))


def get_name(obj):
  """Return the name of an object."""
  return obj.__name__ if hasattr(obj, '__name__') else get_name(type(obj))


# Note that this might BLOAT MEMORY CONSUMPTION since we're holding on
# to every reference ever created by the program without ever releasing
# anything!
class ObjectEncoder:
  def __init__(self):
    # Key: canonicalized small ID
    # Value: encoded (compound) heap object
    self.encoded_heap_objects = {}

    self.id_to_small_IDs = {}
    self.cur_small_ID = 1


  def get_heap(self):
    return self.encoded_heap_objects


  def reset_heap(self):
    # VERY IMPORTANT to reassign to an empty dict rather than just
    # clearing the existing dict, since get_heap() could have been
    # called earlier to return a reference to a previous heap state
    self.encoded_heap_objects = {}

  def set_function_parent_frame_ID(self, ref_obj, enclosing_frame_id):
    assert ref_obj[0] == 'REF'
    func_obj = self.encoded_heap_objects[ref_obj[1]]
    assert func_obj[0] == 'FUNCTION'
    func_obj[-1] = enclosing_frame_id


  # return either a primitive object or an object reference;
  # and as a side effect, update encoded_heap_objects
  def encode(self, dat, get_parent):
    """Encode a data value DAT using the GET_PARENT function for parent ids."""
    # primitive type
    if type(dat) in (int, long, float, str, bool, type(None)):
      if type(dat) is float:
        return round(dat, FLOAT_PRECISION)
      else:
        return dat

    # compound type - return an object reference and update encoded_heap_objects
    else:
      my_id = id(dat)

      try:
        my_small_id = self.id_to_small_IDs[my_id]
      except KeyError:
        my_small_id = self.cur_small_ID
        self.id_to_small_IDs[my_id] = self.cur_small_ID
        self.cur_small_ID += 1

      del my_id # to prevent bugs later in this function

      ret = ['REF', my_small_id]

      # punt early if you've already encoded this object
      if my_small_id in self.encoded_heap_objects:
        return ret


      # major side-effect!
      new_obj = []
      self.encoded_heap_objects[my_small_id] = new_obj

      typ = type(dat)

      if typ == list:
        new_obj.append('LIST')
        for e in dat:
          new_obj.append(self.encode(e, get_parent))
      elif typ == tuple:
        new_obj.append('TUPLE')
        for e in dat:
          new_obj.append(self.encode(e, get_parent))
      elif typ == set:
        new_obj.append('SET')
        for e in dat:
          new_obj.append(self.encode(e, get_parent))
      elif typ == dict:
        new_obj.append('DICT')
        for (k, v) in dat.items():
          # don't display some built-in locals ...
          if k not in ('__module__', '__return__', '__locals__'):
            new_obj.append([self.encode(k, get_parent), self.encode(v, get_parent)])
      elif typ in (types.FunctionType, types.MethodType):
        if is_python3:
          argspec = inspect.getfullargspec(dat)
        else:
          argspec = inspect.getargspec(dat)

        printed_args = [e for e in argspec.args]
        if argspec.varargs:
          printed_args.append('*' + argspec.varargs)

        if is_python3:
          if argspec.varkw:
            printed_args.append('**' + argspec.varkw)
          if argspec.kwonlyargs:
            printed_args.extend(argspec.kwonlyargs)
        else:
          if argspec.keywords:
            printed_args.append('**' + argspec.keywords)

        func_name = get_name(dat)
        pretty_name = func_name + '(' + ', '.join(printed_args) + ')'
        encoded_val = ['FUNCTION', pretty_name, None]
        if get_parent:
          enclosing_frame_id = get_parent(dat)
          encoded_val[2] = enclosing_frame_id
        new_obj.extend(encoded_val)
      elif typ is types.BuiltinFunctionType:
        pretty_name = get_name(dat) + '(...)'
        new_obj.extend(['FUNCTION', pretty_name, None])
      elif is_class(dat) or is_instance(dat):
        self.encode_class_or_instance(dat, new_obj)
      elif typ is types.ModuleType:
        new_obj.extend(['module', dat.__name__])
      else:
        typeStr = str(typ)
        m = typeRE.match(typeStr)

        if not m:
          m = classRE.match(typeStr)

        assert m, typ
        new_obj.extend([m.group(1), str(dat)])

      return ret


  def encode_class_or_instance(self, dat, new_obj):
    """Encode dat as a class or instance."""
    if is_instance(dat):
      if hasattr(dat, '__class__'):
        # common case ...
        class_name = get_name(dat.__class__)
      else:
        # super special case for something like
        # "from datetime import datetime_CAPI" in Python 3.2,
        # which is some weird 'PyCapsule' type ...
        # http://docs.python.org/release/3.1.5/c-api/capsule.html
        class_name = get_name(type(dat))

      new_obj.extend(['INSTANCE', class_name])
      # don't traverse inside modules, or else risk EXPLODING the visualization
      if class_name == 'module':
        return
    else:
      superclass_names = [e.__name__ for e in dat.__bases__ if e is not object]
      new_obj.extend(['CLASS', get_name(dat), superclass_names])

    # traverse inside of its __dict__ to grab attributes
    # (filter out useless-seeming ones):
    hidden = ('__doc__', '__module__', '__return__', '__dict__',
        '__locals__', '__weakref__')
    if hasattr(dat, '__dict__'):
      user_attrs = sorted([e for e in dat.__dict__ if e not in hidden])
    else:
      user_attrs = []

    for attr in user_attrs:
      new_obj.append([self.encode(attr, None), self.encode(dat.__dict__[attr], None)])

