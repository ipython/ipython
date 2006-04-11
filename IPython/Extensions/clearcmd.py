# -*- coding: utf-8 -*-
""" IPython extension: add %clear magic """

import IPython.ipapi
ip = IPython.ipapi.get()


def clear_f(self,arg):
    """ Clear various data (e.g. stored history data)
    
    %clear out - clear output history
    %clear in  - clear input history
    """
    
    api = self.getapi()
    for target in arg.split():
        if target == 'out':
            print "Flushing output cache (%d entries)" % len(api.user_ns()['_oh'])
            self.outputcache.flush()
        elif target == 'in':
            print "Flushing input history"
            from IPython import iplib
            del self.input_hist[:]
            del self.input_hist_raw[:]
            for n in range(1,self.outputcache.prompt_count + 1):
                key = '_i'+`n`
                try:
                    del self.user_ns[key]
                except: pass

ip.expose_magic("clear",clear_f)
    



