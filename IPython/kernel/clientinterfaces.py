# encoding: utf-8

"""General client interfaces."""

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

from zope.interface import Interface, implements

class IFCClientInterfaceProvider(Interface):

    def remote_get_client_name():
        """Return a string giving the class which implements a client-side interface.
        
        The client side of any foolscap connection initially gets a remote reference.
        Some class is needed to adapt that reference to an interface.  This...
        """

class IBlockingClientAdaptor(Interface):
    
    def adapt_to_blocking_client():
        """"""