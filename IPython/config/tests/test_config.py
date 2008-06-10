"""
# Test utilities

>>> import os

>>> def dict_as_sorted_list(d):
...     for k in d:
...         if isinstance(d[k],dict):
...             d[k] = dict_as_sorted_list(d[k])
...     return sorted(d.items())

>>> def pprint(d,level=0):
...     if isinstance(d,dict):
...         d = dict_as_sorted_list(d)
...     for item,value in d:
...         if isinstance(value,list):
...             print "%s%s" % (' '*level, item)
...             pprint(value,level+2)
...         else:
...             print "%s%s: %s" % (' '*level, item, value)


# Tests

>>> from IPython.config.api import *
>>> from sample_config import *

>>> s = Sample()
>>> print s.my_float
3.0
>>> s.my_float = 4
>>> print s.my_float
4.0
>>> print type(s.my_float)
<type 'float'>
>>> s.SubSample.SubSubSample.my_int = 5.0
>>> print s.SubSample.SubSubSample.my_int
5

>>> i = ConfigInspector(s)
>>> print i.properties
[('my_choice', 'a'), ('my_float', 4.0)]
>>> print tuple(s for s,v in i.subconfigs)
('MiddleSection', 'SubSample')

>>> print s
my_float = 4.0
<BLANKLINE>
[SubSample]
<BLANKLINE>
  [[SubSubSample]]
    my_int = 5
<BLANKLINE>

>>> import tempfile
>>> fn = tempfile.mktemp()
>>> f = open(fn,'w')
>>> f.write(str(s))
>>> f.close()

>>> s += fn

>>> from IPython.external.configobj import ConfigObj
>>> c = ConfigObj(fn)
>>> c['SubSample']['subsample_uri'] = 'http://ipython.scipy.org'

>>> s += c
>>> print s
my_float = 4.0
<BLANKLINE>
[SubSample]
  subsample_uri = 'http://ipython.scipy.org'
<BLANKLINE>
  [[SubSubSample]]
    my_int = 5
<BLANKLINE>

>>> pprint(dict_from_config(s,only_modified=False))
MiddleSection
  left_alone: '1'
  unknown_mod: 'asd'
SubSample
  SubSubSample
    my_int: 5
  subsample_uri: 'http://ipython.scipy.org'
my_choice: 'a'
my_float: 4.0

>>> pprint(dict_from_config(s))
SubSample
  SubSubSample
    my_int: 5
  subsample_uri: 'http://ipython.scipy.org'
my_float: 4.0

Test roundtripping:

>>> fn = tempfile.mktemp()
>>> f = open(fn, 'w')
>>> f.write('''
... [MiddleSection]
... # some comment here
... left_alone = 'c'
... ''')
>>> f.close()

>>> s += fn

>>> pprint(dict_from_config(s))
MiddleSection
  left_alone: 'c'
SubSample
  SubSubSample
    my_int: 5
  subsample_uri: 'http://ipython.scipy.org'
my_float: 4.0

>>> write(s, fn)
>>> f = file(fn,'r')
>>> ConfigInspector(s).reset()
>>> pprint(dict_from_config(s))

>>> s += fn
>>> os.unlink(fn)
>>> pprint(dict_from_config(s))
MiddleSection
  left_alone: 'c'
SubSample
  SubSubSample
    my_int: 5
  subsample_uri: 'http://ipython.scipy.org'
my_float: 4.0


"""
