"""PendingResult objects for the client"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import error

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class PendingResult(object):
    """Class for representing results of non-blocking calls."""
    def __init__(self, client, msg_ids):
        self.client = client
        self.msg_ids = msg_ids
        self._result = None
        self.done = False
    
    def __repr__(self):
        if self.done:
            return "<%s: finished>"%(self.__class__.__name__)
        else:
            return "<%s: %r>"%(self.__class__.__name__,self.msg_ids)
    
    @property
    def result(self):
        if self._result is not None:
            return self._result
        if not self.done:
            self.wait(0)
        if self.done:
            results = map(self.client.results.get, self.msg_ids)
            results = error.collect_exceptions(results, 'get_result')
            self._result = self.reconstruct_result(results)
            return self._result
        else:
            raise error.ResultNotCompleted
    
    def reconstruct_result(self, res):
        """
        Override me in subclasses for turning a list of results
        into the expected form.
        """
        if len(res) == 1:
            return res[0]
        else:
            return res
    
    def wait(self, timout=-1):
        self.done = self.client.barrier(self.msg_ids)
        return self.done

class PendingMapResult(PendingResult):
    """Class for representing results of non-blocking gathers.
    
    This will properly reconstruct the gather.
    """
    
    def __init__(self, client, msg_ids, mapObject):
        self.mapObject = mapObject
        PendingResult.__init__(self, client, msg_ids)
    
    def reconstruct_result(self, res):
        """Perform the gather on the actual results."""
        return self.mapObject.joinPartitions(res)
    
        
