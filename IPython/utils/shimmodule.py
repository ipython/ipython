"""A shim module for deprecated imports
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys
import types

class ShimModule(types.ModuleType):

    def __init__(self, *args, **kwargs):
        self._mirror = kwargs.pop("mirror")
        super(ShimModule, self).__init__(*args, **kwargs)
        if sys.version_info >= (3,4):
            self.__spec__ = __import__(self._mirror).__spec__

    def __getattr__(self, key):
        # Use the equivalent of import_item(name), see below
        name = "%s.%s" % (self._mirror, key)

        # NOTE: the code below was copied *verbatim* from
        # importstring.import_item. For some very strange reason that makes no
        # sense to me, if we call it *as a function*, it doesn't work.  This
        # has something to do with the deep bowels of the import machinery and
        # I couldn't find a way to make the code work as a standard function
        # call.  But at least since it's an unmodified copy of import_item,
        # which is used extensively and has a test suite, we can be reasonably
        # confident this is OK.  If anyone finds how to call the function, all
        # the below could be replaced simply with:
        #
        # from IPython.utils.importstring import import_item
        # return import_item('MIRROR.' + key)

        parts = name.rsplit('.', 1)
        if len(parts) == 2:
            # called with 'foo.bar....'
            package, obj = parts
            module = __import__(package, fromlist=[obj])
            return getattr(module, obj)
        else:
            # called with un-dotted string
            return __import__(parts[0])
