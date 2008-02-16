# -*- coding: utf-8 -*-

import IPython.ipapi
ip = IPython.ipapi.get()

def ${name}_f(self, arg):
    r""" Short explanation
    
    Long explanation, examples
    
    """
    
    # opts,args = self.parse_options(arg,'rx')
    # if 'r' in opts: pass
    
    

ip.expose_magic("${name}",${name}_f)        
    
    
