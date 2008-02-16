# -*- coding: utf-8 -*-
""" IPython extension: add %clear magic """

import IPython.ipapi
import gc
ip = IPython.ipapi.get()


def clear_f(self,arg):
    """ Clear various data (e.g. stored history data)
    
    %clear out - clear output history
    %clear in  - clear input history
    %clear shadow_compress - Compresses shadow history (to speed up ipython)
    %clear shadow_nuke - permanently erase all entries in shadow history
    %clear dhist - clear dir history
    """
    
    api = self.getapi()
    for target in arg.split():
        if target == 'out':
            print "Flushing output cache (%d entries)" % len(api.user_ns['_oh'])
            self.outputcache.flush()
        elif target == 'in':
            print "Flushing input history"
            from IPython import iplib
            pc = self.outputcache.prompt_count + 1
            for n in range(1, pc):
                key = '_i'+`n`
                try:
                    del self.user_ns[key]
                except: pass
            # must be done in-place
            self.input_hist[:] = ['\n'] * pc 
            self.input_hist_raw[:] = ['\n'] * pc
        elif target == 'array':
            try:
                pylab=ip.IP.pylab
                for x in self.user_ns.keys():
                    if isinstance(self.user_ns[x],pylab.arraytype):
                        del self.user_ns[x]
            except AttributeError:
                print "Clear array only available in -pylab mode"
            gc.collect()                

        elif target == 'shadow_compress':
            print "Compressing shadow history"
            api.db.hcompress('shadowhist')
            
        elif target == 'shadow_nuke':
            print "Erased all keys from shadow history "
            for k in ip.db.keys('shadowhist/*'):
                del ip.db[k]
        elif target == 'dhist':
            print "Clearing directory history"
            del ip.user_ns['_dh'][:]

            
ip.expose_magic("clear",clear_f)
import ipy_completers
ipy_completers.quick_completer(
 '%clear','in out shadow_nuke shadow_compress dhist')
    



