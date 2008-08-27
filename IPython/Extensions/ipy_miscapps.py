""" Completers for miscellaneous command line apps

"""
import IPython.ipapi
ip = IPython.ipapi.get()
import os

def surfraw_completer(self,cmdline):
    """ Completer for 'surfraw'

    example::
      sr go<tab>  => sr google

    """
    compl = [l.split(None,1)[0] for l in os.popen('sr -elvi')]
    return compl


ip.set_hook('complete_command', surfraw_completer, str_key = 'sr')