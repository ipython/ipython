#!/usr/bin/env python
"""
IPython extension to fix pysh profile
"""

from IPython.core.prefilter import PrefilterHandler, Unicode, PrefilterChecker

class ShellChecker(PrefilterChecker):
    """ shell checker should really run before anything else """
    priority = 1
    def check(self, line_info):
        """ note: the way that line_info splitting happens means
            that for a command like "apt-get foo", first/rest will
            be apt/-get foo.  it's better to just use line_info.line
        """
        if line_info.continue_prompt or not line_info.line.strip():
            return None
        l0 = line_info.line[0]
        if l0 in '~/.' or have_alias(line_info.line.split()[0]):
            return self.prefilter_manager.get_handler_by_name('mine')


class ShellHandler(PrefilterHandler):
    """ShellHandler works basically like the shell transformer"""
    handler_name = Unicode('mine')
    def handle(self, line_info):
        cmd = line_info.line.strip()
        return 'get_ipython().system(%r)' % (cmd, )

def have_alias(x):
    """ this helper function is fairly expensive to be running on
        (almost) every input line.  perhaps it should be cached, but

          a) answers would have to be kept in sync with rehashx calls
          b) the alias list must be getting checked all the time anyway?
    """
    blacklist = ['ed']
    return x not in blacklist and \
           x in [cmd for alias,cmd in get_ipython().alias_manager.aliases]

ip = get_ipython()
cfg = ip.config
pm = ip.prefilter_manager
kargs = dict(
    shell=pm.shell,
    prefilter_manager=pm,
    config=pm.config)
checker = ShellChecker(**kargs)
handler = ShellHandler(**kargs)

def load_ipython_extension(ip):
    """ called by %load_ext magic"""
    # first fix the default handling of shell commands
    ip.prefilter_manager.register_checker(checker)
    ip.prefilter_manager.register_handler(handler.handler_name, handler, [])

def unload_ipython_extension(ip):
    """ called by %unload_ext magic"""
    # are singletons involved here?  not sure we can use
    # manager.unregister_handler() etc, since it does an
    # instance check instead of a class check.
    handler_list= ip.prefilter_manager._handlers
    del handler_list[handler.handler_name]
    checker_list = ip.prefilter_manager._checkers
    for tmp in checker_list:
        if isinstance(tmp, ShellChecker):
            del checker_list[checker_list.index(tmp)]
