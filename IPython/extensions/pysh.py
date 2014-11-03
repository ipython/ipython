#!/usr/bin/env python
"""
IPython extension to fix pysh profile
"""
from IPython.core.prefilter import PrefilterHandler, Unicode, PrefilterChecker

HANDLER_NAME = 'ShellHandler'


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
            return self.prefilter_manager.get_handler_by_name(HANDLER_NAME)


class ShellHandler(PrefilterHandler):
    """ ShellHandler changes certain lines to system calls """
    handler_name = Unicode(HANDLER_NAME)

    def handle(self, line_info):
        cmd = line_info.line.strip()
        return 'get_ipython().system(%r)' % (cmd, )


def have_alias(x):
    """ this helper function is fairly expensive to be running on
        (almost) every input line.  perhaps it should be cached, but

          a) answers would have to be kept in sync with rehashx calls
          b) the alias list must be getting checked all the time anyway?
    """
    blacklist = [
        'ed',   # posix line oriented, not as useful as ipython edit
        'from', # posix mail tool, screws up python "from x import y"
        'ip',   # often used as in ip=get_ipython()
        ]
    if x in blacklist:
        return False
    else:
        alias_list = get_ipython().alias_manager.aliases
        cmd_list = [cmd for alias, cmd in alias_list]
        return x in cmd_list


def load_ipython_extension(ip):
    """ called by %load_ext magic"""
    ip = get_ipython()
    pm = ip.prefilter_manager
    kargs = dict(
        shell=pm.shell,
        prefilter_manager=pm,
        config=pm.config)
    checker = ShellChecker(**kargs)
    handler = ShellHandler(**kargs)
    ip.prefilter_manager.register_checker(checker)
    ip.prefilter_manager.register_handler(HANDLER_NAME, handler, [])
    return checker, handler


def unload_ipython_extension(ip):
    """ called by %unload_ext magic"""
    # are singletons involved here?  not sure we can use
    # manager.unregister_handler() etc, since it does an
    # instance check instead of a class check.
    ip = get_ipython()
    handlers = ip.prefilter_manager.handlers
    for handler_name, handler in handlers.items():
        if isinstance(handler, ShellHandler):
            break
    del handlers[handler_name]
    checker_list = ip.prefilter_manager._checkers
    for tmp in checker_list:
        if isinstance(tmp, ShellChecker):
            del checker_list[checker_list.index(tmp)]
