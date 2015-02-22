"""
The common code for checking message specification. 
This can be used in the tests to verify messages.

These will remain same between different versions of
message specification.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import re
import sys
from distutils.version import LooseVersion as V

import nose.tools as nt

from IPython.utils.traitlets import (
    HasTraits, TraitError, Bool, Unicode, Dict, Integer, List, Enum,
)
from IPython.utils.py3compat import string_types, iteritems

#-----------------------------------------------------------------------------
# Message Spec References
#-----------------------------------------------------------------------------

class Reference(HasTraits):

    """
    Base class for message spec specification testing.

    This class is the core of the message specification test.  The
    idea is that child classes implement trait attributes for each
    message keys, so that message keys can be tested against these
    traits using :meth:`check` method.

    """

    def check(self, d):
        """validate a dict against our traits"""
        for key in self.trait_names():
            nt.assert_in(key, d)
            # FIXME: always allow None, probably not a good idea
            if d[key] is None:
                continue
            try:
                setattr(self, key, d[key])
            except TraitError as e:
                assert False, str(e)


class Version(Unicode):
    def __init__(self, *args, **kwargs):
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        kwargs['default_value'] = self.min
        super(Version, self).__init__(*args, **kwargs)
    
    def validate(self, obj, value):
        if self.min and V(value) < V(self.min):
            raise TraitError("bad version: %s < %s" % (value, self.min))
        if self.max and (V(value) > V(self.max)):
            raise TraitError("bad version: %s > %s" % (value, self.max))

mime_pat = re.compile(r'^[\w\-\+\.]+/[\w\-\+\.]+$')

class MimeBundle(Reference):
    metadata = Dict()
    data = Dict()
    def _data_changed(self, name, old, new):
        for k,v in iteritems(new):
            assert mime_pat.match(k)
            nt.assert_is_instance(v, string_types)
