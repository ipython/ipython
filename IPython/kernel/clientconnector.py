# encoding: utf-8

"""A class for handling client connections to the controller."""

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

from twisted.internet import defer

from IPython.kernel.fcutil import Tub, UnauthenticatedTub

from IPython.kernel.config import config_manager as kernel_config_manager
from IPython.config.cutils import import_item
from IPython.kernel.fcutil import find_furl

co = kernel_config_manager.get_config_obj()
client_co = co['client']

#-------------------------------------------------------------------------------
# The ClientConnector class
#-------------------------------------------------------------------------------

class ClientConnector(object):
    """
    This class gets remote references from furls and returns the wrapped clients.
    
    This class is also used in `client.py` and `asyncclient.py` to create 
    a single per client-process Tub.
    """
    
    def __init__(self):
        self._remote_refs = {}
        self.tub = Tub()
        self.tub.startService()
    
    def get_reference(self, furl_or_file):
        """
        Get a remote reference using a furl or a file containing a furl.
        
        Remote references are cached locally so once a remote reference
        has been retrieved for a given furl, the cached version is 
        returned.
        
        :Parameters:
            furl_or_file : str
                A furl or a filename containing a furl
        
        :Returns:
            A deferred to a remote reference
        """
        furl = find_furl(furl_or_file)
        if furl in self._remote_refs:
            d = defer.succeed(self._remote_refs[furl])
        else:
            d = self.tub.getReference(furl)
            d.addCallback(self.save_ref, furl)
        return d
        
    def save_ref(self, ref, furl):
        """
        Cache a remote reference by its furl.
        """
        self._remote_refs[furl] = ref
        return ref
        
    def get_task_client(self, furl_or_file=''):
        """
        Get the task controller client.
        
        This method is a simple wrapper around `get_client` that allow
        `furl_or_file` to be empty, in which case, the furls is taken
        from the default furl file given in the configuration.
        
        :Parameters:
            furl_or_file : str
                A furl or a filename containing a furl.  If empty, the
                default furl_file will be used
                
        :Returns:
            A deferred to the actual client class
        """
        task_co = client_co['client_interfaces']['task']
        if furl_or_file:
            ff = furl_or_file
        else:
            ff = task_co['furl_file']
        return self.get_client(ff)

    def get_multiengine_client(self, furl_or_file=''):
        """
        Get the multiengine controller client.
        
        This method is a simple wrapper around `get_client` that allow
        `furl_or_file` to be empty, in which case, the furls is taken
        from the default furl file given in the configuration.
        
        :Parameters:
            furl_or_file : str
                A furl or a filename containing a furl.  If empty, the
                default furl_file will be used
                
        :Returns:
            A deferred to the actual client class
        """
        task_co = client_co['client_interfaces']['multiengine']
        if furl_or_file:
            ff = furl_or_file
        else:
            ff = task_co['furl_file']
        return self.get_client(ff)
    
    def get_client(self, furl_or_file):
        """
        Get a remote reference and wrap it in a client by furl.
        
        This method first gets a remote reference and then calls its 
        `get_client_name` method to find the apprpriate client class
        that should be used to wrap the remote reference.
        
        :Parameters:
            furl_or_file : str
                A furl or a filename containing a furl
        
        :Returns:
            A deferred to the actual client class
        """
        furl = find_furl(furl_or_file)
        d = self.get_reference(furl)
        def wrap_remote_reference(rr):
            d = rr.callRemote('get_client_name')
            d.addCallback(lambda name: import_item(name))
            def adapt(client_interface):
                client = client_interface(rr)
                client.tub = self.tub
                return client
            d.addCallback(adapt)

            return d
        d.addCallback(wrap_remote_reference)
        return d
