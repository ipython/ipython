""" ZMQ Kernel History accessor and manager. """
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011 The IPython Development Team.
#
#  Distributed under the terms of the BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.history import HistoryAccessorBase
from IPython.utils import py3compat
from IPython.utils.traitlets import Dict, List

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

class ZMQHistoryManager(HistoryAccessorBase):
    """History accessor and manager for ZMQ-based kernels"""
    input_hist_parsed = List([""])
    output_hist = Dict()
    dir_hist = List()
    output_hist_reprs = Dict()

    def __init__(self, client):
        """
        Class to load the command-line history from a ZMQ-based kernel,
        and access the history.

        Parameters
        ----------

        client: `IPython.kernel.KernelClient`
          The kernel client in order to request the history.
        """
        self.client = client

    def _load_history(self, raw=True, output=False, hist_access_type='range',
                      **kwargs):
        """
        Load the history over ZMQ from the kernel. Wraps the history
        messaging with loop to wait to get history results.
        """
        # 'range' (fill in session, start and stop params), 
        # 'tail' (fill in n)
        # 'search' (fill in pattern param).
        msg_id = self.client.history(raw=raw, output=output, 
                                     hist_access_type=hist_access_type, 
                                     **kwargs)
        history = []
        while True:
            try:
                reply = self.client.get_shell_msg(timeout=1)
            except Empty:
                break
            else:
                if reply['parent_header'].get('msg_id') == msg_id:
                    history = reply['content'].get('history', [])
                    break
        return history

    def writeout_cache(self):
        """
        Not needed for ZMQ-based histories.
        """
        pass

    def get_tail(self, n=10, raw=True, output=False, include_latest=False):
        return self._load_history(hist_access_type='tail', n=n, raw=raw, 
                                  output=output)

    def search(self, pattern="*", raw=True, search_raw=True,
               output=False, n=None, unique=False):
        return self._load_history(hist_access_type='search', pattern=pattern, 
                                  raw=raw, search_raw=search_raw, 
                                  output=output, n=n, unique=unique)

    def get_range(self, session, start=1, stop=None, raw=True,output=False):
        return self._load_history(hist_access_type='range', raw=raw, 
                                  output=output, start=start, stop=stop,
                                  session=session)

    def get_range_by_str(self, rangestr, raw=True, output=False):
        return self._load_history(hist_access_type='range', raw=raw, 
                                  output=output, rangestr=rangetr)

    def end_session(self):
        """
        Nothing to do for ZMQ-based histories.
        """
        pass

    def reset(self, new_session=True):
        """Clear the session history, releasing all object references, and
        optionally open a new session."""
        self.output_hist.clear()
        # The directory history can't be completely empty
        self.dir_hist[:] = [py3compat.getcwd()]
        
        if new_session:
            if self.session_number:
                self.end_session()
            self.input_hist_parsed[:] = [""]
            self.input_hist_raw[:] = [""]
            self.new_session()

