"""Traitlets -- a light-weight meta-class free stand-in for Traits.

Traitlet behaviour
==================
- Automatic casting, equivalent to traits.C* classes, e.g. CFloat, CBool etc.

- By default, validation is done by attempting to cast a given value
  to the underlying type, e.g. bool for Bool, float for Float etc.

- To set or get a Traitlet value, use the ()-operator.  E.g.

  >>> b = Bool(False)
  >>> b(True)
  >>> print b # returns a string representation of the Traitlet
  True
  >>> print b() # returns the underlying bool object
  True

  This makes it possible to change values "in-place", unlike an assigment
  of the form

  >>> c = Bool(False)
  >>> c = True

  which results in

  >>> print type(b), type(c)
  <class 'IPython.config.traitlets.Bool'> <type 'bool'>

- Each Traitlet keeps track of its modification state, e.g.

  >>> c = Bool(False)
  >>> print c.modified
  False
  >>> c(False)
  >>> print c.modified
  False
  >>> c(True)
  >>> print c.modified
  True

How to customize Traitlets
==========================

The easiest way to create a new Traitlet is by wrapping an underlying
Python type.  This is done by setting the "_type" class attribute.  For
example, creating an int-like Traitlet is done as follows:

>>> class MyInt(Traitlet):
...     _type = int

>>> i = MyInt(3)
>>> i(4)
>>> print i
4

>>> try:
...     i('a')
... except ValidationError:
...    pass # this is expected
... else:
...     "This should not be reached."

Furthermore, the following methods are provided for finer grained
control of validation and assignment:

 - validate(self,value)
   Ensure that "value" is valid.  If not, raise an exception of any kind
   with a suitable error message, which is reported to the user.

 - prepare_value(self)
   When using the ()-operator to query the underlying Traitlet value,
   that value is first passed through prepare_value.  For example:

   >>> class Eval(Traitlet):
   ...     _type = str
   ...
   ...     def prepare_value(self):
   ...         return eval(self._value)

   >>> x = Eval('1+1')
   >>> print x
   '1+1'
   >>> print x()
   2

 - __repr__(self)
   By default, repr(self._value) is returned.  This can be customised
   to, for example, first call prepare_value and return the repr of
   the resulting object.

"""

import re
import types

class ValidationError(Exception):
    pass

class Traitlet(object):
    """Traitlet which knows its modification state.

    """
    def __init__(self, value):
        "Validate and store the default value.  State is 'unmodified'."
        self._type = getattr(self,'_type',None)
        value = self._parse_validation(value)
        self._default_value = value
        self.reset()

    def reset(self):
        self._value = self._default_value
        self._changed = False

    def validate(self, value):
        "Validate the given value."
        if self._type is not None:
            self._type(value)

    def _parse_validation(self, value):
        """Run validation and return a descriptive error if needed.

        """
        try:
            self.validate(value)
        except Exception, e:
            err_message = 'Cannot convert "%s" to %s' % \
                          (value, self.__class__.__name__.lower())
            if e.message:
                err_message += ': %s' % e.message
            raise ValidationError(err_message)
        else:
            # Cast to appropriate type before storing
            if self._type is not None:
                value = self._type(value)
            return value

    def prepare_value(self):
        """Run on value before it is ever returned to the user.

        """
        return self._value

    def __call__(self,value=None):
        """Query or set value depending on whether `value` is specified.

        """
        if value is None:
            return self.prepare_value()

        self._value = self._parse_validation(value)
        self._changed = (self._value != self._default_value)

    @property
    def modified(self):
        "Whether value has changed from original definition."
        return self._changed

    def __repr__(self):
        """This class is represented by the underlying repr.  Used when
        dumping value to file.

        """
        return repr(self._value)

class Float(Traitlet):
    """
    >>> f = Float(0)
    >>> print f.modified
    False

    >>> f(3)
    >>> print f()
    3.0
    >>> print f.modified
    True

    >>> f(0)
    >>> print f()
    0.0
    >>> print f.modified
    False

    >>> try:
    ...    f('a')
    ... except ValidationError:
    ...    pass

    """
    _type = float

class Enum(Traitlet):
    """
    >>> c = Enum('a','b','c')
    >>> print c()
    a

    >>> try:
    ...    c('unknown')
    ... except ValidationError:
    ...    pass

    >>> print c.modified
    False

    >>> c('b')
    >>> print c()
    b

    """
    def __init__(self, *options):
        self._options = options
        super(Enum,self).__init__(options[0])

    def validate(self, value):
        if not value in self._options:
            raise ValueError('must be one of %s' % str(self._options))

class Module(Traitlet):
    """
    >>> m = Module('some.unknown.module')
    >>> print m
    'some.unknown.module'

    >>> m = Module('re')
    >>> assert type(m()) is types.ModuleType

    """
    _type = str

    def prepare_value(self):
        try:
            module = eval(self._value)
        except:
            module = None

        if type(module) is not types.ModuleType:
            raise ValueError("Invalid module name: %s" % self._value)
        else:
            return module


class URI(Traitlet):
    """
    >>> u = URI('http://')

    >>> try:
    ...    u = URI('something.else')
    ... except ValidationError:
    ...    pass

    >>> u = URI('http://ipython.scipy.org/')
    >>> print u
    'http://ipython.scipy.org/'

    """
    _regexp = re.compile(r'^[a-zA-Z]+:\/\/')
    _type = str

    def validate(self, uri):
        if not self._regexp.match(uri):
            raise ValueError()

class Int(Traitlet):
    """
    >>> i = Int(3.5)
    >>> print i
    3
    >>> print i()
    3

    >>> i = Int('4')
    >>> print i
    4

    >>> try:
    ...    i = Int('a')
    ... except ValidationError:
    ...    pass
    ... else:
    ...    raise "Should fail"

    """
    _type = int

class Bool(Traitlet):
    """
    >>> b = Bool(2)
    >>> print b
    True
    >>> print b()
    True

    >>> b = Bool('True')
    >>> print b
    True
    >>> b(True)
    >>> print b.modified
    False

    >>> print Bool(0)
    False

    """
    _type = bool

class Unicode(Traitlet):
    """
    >>> u = Unicode(123)
    >>> print u
    u'123'

    >>> u = Unicode('123')
    >>> print u.modified
    False

    >>> u('hello world')
    >>> print u
    u'hello world'

    """
    _type = unicode
