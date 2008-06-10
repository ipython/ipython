"""Load and store configuration objects.

Test this module using

nosetests -v --with-doctest --doctest-tests IPython.config

"""

from __future__ import with_statement
from contextlib import contextmanager

import inspect
import types
from IPython.config import traitlets
from traitlets import Traitlet
from IPython.external.configobj import ConfigObj

def debug(s):
    import sys
    sys.stderr.write(str(s) + '\n')

@contextmanager
def raw(config):
    """Context manager for accessing traitlets directly.

    """
    config.__getattribute__('',raw_access=True)
    yield config
    config.__getattribute__('',raw_access=False)

class Config(object):
    """
    Implementation Notes
    ====================
    All instances of the same Config class share properties.  Therefore,

    >>> class Sample(Config):
    ...     my_float = traitlets.Float(3)

    >>> s0 = Sample()
    >>> s1 = Sample()
    >>> s0.my_float = 5
    >>> s0.my_float == s1.my_float
    True

    """
    def __init__(self):
        # Instantiate subconfigs
        with raw(self):
            subconfigs = [(n,v) for n,v in
                          inspect.getmembers(self, inspect.isclass)
                          if not n.startswith('__')]

        for n,v in subconfigs:
            setattr(self, n, v())

    def __getattribute__(self,attr,raw_access=None,
                         _ns={'raw_access':False}):
        if raw_access is not None:
            _ns['raw_access'] = raw_access
            return

        obj = object.__getattribute__(self,attr)
        if isinstance(obj,Traitlet) and not _ns['raw_access']:
            return obj.__call__()
        else:
            return obj

    def __setattr__(self,attr,value):
        obj = object.__getattribute__(self,attr)
        if isinstance(obj,Traitlet):
            obj(value)
        else:
            self.__dict__[attr] = value

    def __str__(self,level=1,only_modified=True):
        ci = ConfigInspector(self)
        out = ''
        spacer = '  '*(level-1)

        # Add traitlet representations
        for p,v in ci.properties:
            if (v.modified and only_modified) or not only_modified:
                out += spacer + '%s = %s\n' % (p,v)

        # Add subconfig representations
        for (n,v) in ci.subconfigs:
            sub_str = v.__str__(level=level+1,only_modified=only_modified)
            if sub_str:
                out += '\n' + spacer + '[' * level + ('%s' % n) \
                       + ']'*level + '\n'
                out += sub_str

        return out

    def __iadd__(self,source):
        """Load configuration from filename, and update self.

        """
        if not isinstance(source,dict):
            source = ConfigObj(source, unrepr=True)
        update_from_dict(self,source)
        return self


class ConfigInspector(object):
    """Allow the inspection of Config objects.

    """
    def __init__(self,config):
        self._config = config

    @property
    def properties(self):
        "Return all traitlet names."
        with raw(self._config):
            return inspect.getmembers(self._config,
                                      lambda obj: isinstance(obj, Traitlet))

    @property
    def subconfigs(self):
        "Return all subconfig names and values."
        with raw(self._config):
            return [(n,v) for n,v in
                    inspect.getmembers(self._config,
                                       lambda obj: isinstance(obj,Config))
                    if not n.startswith('__')]

    def reset(self):
        for (p,v) in self.properties:
            v.reset()

        for (s,v) in self.subconfigs:
            ConfigInspector(v).reset()

def update_from_dict(config,d):
    """Propagate the values of the dictionary to the given configuration.

    Useful to load configobj instances.

    """
    for k,v in d.items():
        try:
            prop_or_subconfig = getattr(config, k)
        except AttributeError:
            print "Invalid section/property in config file: %s" % k
        else:
            if isinstance(v,dict):
                update_from_dict(prop_or_subconfig,v)
            else:
                setattr(config, k, v)

def dict_from_config(config,only_modified=True):
    """Create a dictionary from a Config object."""
    ci = ConfigInspector(config)
    out = {}

    for p,v in ci.properties:
        if (v.modified and only_modified) or not only_modified:
            out[p] = v

    for s,v in ci.subconfigs:
        d = dict_from_config(v,only_modified)
        if d != {}:
            out[s] = d

    return out

def write(config, target):
    """Write a configuration to file.

    """
    if isinstance(target, str):
        target = open(target, 'w+')
    target.flush()
    target.seek(0)

    confobj = ConfigObj(dict_from_config(config), unrepr=True)
    confobj.write(target)
