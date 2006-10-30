""" Tab completion support for a couple of linux package managers 

This is also an example of how to write custom completer plugins
or hooks.

Practical use:

[ipython]|1> import ipy_linux_package_managers
[ipython]|2> apt-get u<<< press tab here >>>
update  upgrade
[ipython]|2> apt-get up

"""
import IPython.ipapi

ip = IPython.ipapi.get()

def apt_completers(self, event):
    """ This should return a list of strings with possible completions.
    
    Note that all the included strings that don't start with event.symbol
    are removed, in order to not confuse readline.
    
    """
    # print event # dbg
    
    # commands are only suggested for the 'command' part of package manager
    # invocation
        
    cmd = (event.line + "<placeholder>").rsplit(None,1)[0]
    # print cmd
    if cmd.endswith('apt-get') or cmd.endswith('yum'):
        return ['update', 'upgrade', 'install', 'remove']
    
    # later on, add dpkg -l / whatever to get list of possible 
    # packages, add switches etc. for the rest of command line
    # filling
    
    raise IPython.ipapi.TryNext 


# re_key specifies the regexp that triggers the specified completer

ip.set_hook('complete_command', apt_completers, re_key = '.*apt-get')

ip.set_hook('complete_command', apt_completers, re_key = '.*yum')
    