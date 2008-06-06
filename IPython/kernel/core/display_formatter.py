# encoding: utf-8

"""Objects for replacing sys.displayhook()."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

class IDisplayFormatter(object):
    """ Objects conforming to this interface will be responsible for formatting
    representations of objects that pass through sys.displayhook() during an
    interactive interpreter session.
    """

    # The kind of formatter.
    kind = 'display'

    # The unique identifier for this formatter.
    identifier = None


    def __call__(self, obj):
        """ Return a formatted representation of an object.

        Return None if one cannot return a representation in this format.
        """

        raise NotImplementedError


class ReprDisplayFormatter(IDisplayFormatter):
    """ Return the repr() string representation of an object.
    """

    # The unique identifier for this formatter.
    identifier = 'repr'

    
    def __call__(self, obj):
        """ Return a formatted representation of an object.
        """

        return repr(obj)


class PPrintDisplayFormatter(IDisplayFormatter):
    """ Return a pretty-printed string representation of an object.
    """

    # The unique identifier for this formatter.
    identifier = 'pprint'

    
    def __call__(self, obj):
        """ Return a formatted representation of an object.
        """

        import pprint
        return pprint.pformat(obj)


