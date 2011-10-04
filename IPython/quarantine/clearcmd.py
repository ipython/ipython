# -*- coding: utf-8 -*-
""" IPython extension: add %clear magic """

from IPython.core import ipapi
import gc
ip = ipapi.get()

def clear_f(self,arg):
    """ Clear various data (e.g. stored history data)

    %clear in  - clear input history
    %clear out - clear output history
    %clear shadow_compress - Compresses shadow history (to speed up ipython)
    %clear shadow_nuke - permanently erase all entries in shadow history
    %clear dhist - clear dir history
    %clear array - clear only variables that are NumPy arrays

    Examples:

    In [1]: clear in
    Flushing input history

    In [2]: clear shadow_compress
    Compressing shadow history

    In [3]: clear shadow_nuke
    Erased all keys from shadow history

    In [4]: clear dhist
    Clearing directory history
    """

    api = self.getapi()
    user_ns = self.user_ns  # local lookup, heavily used


    for target in arg.split():

        if target == 'out':
            print "Flushing output cache (%d entries)" % len(user_ns['_oh'])
            self.outputcache.flush()

        elif target == 'in':
            print "Flushing input history"
            pc = self.outputcache.prompt_count + 1
            for n in range(1, pc):
                key = '_i'+`n`
                user_ns.pop(key,None)
                try:
                    del user_ns[key]
                except: pass
            # must be done in-place
            self.history_manager.input_hist_parsed[:] = ['\n'] * pc
            self.history_manager.input_hist_raw[:] = ['\n'] * pc

        elif target == 'array':
            # Support cleaning up numpy arrays
            try:
                from numpy import ndarray
                # This must be done with items and not iteritems because we're
                # going to modify the dict in-place.
                for x,val in user_ns.items():
                    if isinstance(val,ndarray):
                        del user_ns[x]
            except AttributeError:
                print "Clear array only works if Numpy is available."

        elif target == 'shadow_compress':
            print "Compressing shadow history"
            api.db.hcompress('shadowhist')

        elif target == 'shadow_nuke':
            print "Erased all keys from shadow history "
            for k in ip.db.keys('shadowhist/*'):
                del ip.db[k]

        elif target == 'dhist':
            print "Clearing directory history"
            del user_ns['_dh'][:]

    gc.collect()

# Activate the extension
ip.define_magic("clear",clear_f)
import ipy_completers
ipy_completers.quick_completer(
    '%clear','in out shadow_nuke shadow_compress dhist')
