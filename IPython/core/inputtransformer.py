import abc
import re

from IPython.core.splitinput import split_user_input, LineInfo
from IPython.core.inputsplitter import (ESC_SHELL, ESC_SH_CAP, ESC_HELP,
                                        ESC_HELP2, ESC_MAGIC, ESC_MAGIC2,
                                        ESC_QUOTE, ESC_QUOTE2, ESC_PAREN)
from IPython.core.inputsplitter import EscapedTransformer, _make_help_call, has_comment

class InputTransformer(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def push(self, line):
        pass
    
    @abc.abstractmethod
    def reset(self):
        pass

class StatelessInputTransformer(InputTransformer):
    """Decorator for a stateless input transformer implemented as a function."""
    def __init__(self, func):
        self.func = func
    
    def push(self, line):
        return self.func(line)
    
    def reset(self):
        pass

class CoroutineInputTransformer(InputTransformer):
    """Decorator for an input transformer implemented as a coroutine."""
    def __init__(self, coro):
        # Prime it
        self.coro = coro()
        next(self.coro)
    
    def push(self, line):
        return self.coro.send(line)
    
    def reset(self):
        self.coro.send(None)

@CoroutineInputTransformer
def escaped_transformer():
    et = EscapedTransformer()
    line = ''
    while True:
        line = (yield line)
        if not line or line.isspace():
            continue
        lineinf = LineInfo(line)
        if lineinf.esc not in et.tr:
            continue
        
        parts = []
        while line is not None:
            parts.append(line.rstrip('\\'))
            if not line.endswith('\\'):
                break
            line = (yield None)
        
        # Output
        lineinf = LineInfo(' '.join(parts))
        line = et.tr[lineinf.esc](lineinf)

_initial_space_re = re.compile(r'\s*')

_help_end_re = re.compile(r"""(%{0,2}
                              [a-zA-Z_*][\w*]*        # Variable name
                              (\.[a-zA-Z_*][\w*]*)*   # .etc.etc
                              )
                              (\?\??)$                # ? or ??""",
                              re.VERBOSE)

@StatelessInputTransformer
def transform_help_end(line):
    """Translate lines with ?/?? at the end"""
    m = _help_end_re.search(line)
    if m is None or has_comment(line):
        return line
    target = m.group(1)
    esc = m.group(3)
    lspace = _initial_space_re.match(line).group(0)

    # If we're mid-command, put it back on the next prompt for the user.
    next_input = line.rstrip('?') if line.strip() != m.group(0) else None

    return _make_help_call(target, esc, lspace, next_input)
    
                
@CoroutineInputTransformer
def cellmagic():
    tpl = 'get_ipython().run_cell_magic(%r, %r, %r)'
    line = ''
    while True:
        line = (yield line)
        if not line.startswith(ESC_MAGIC2):
            continue
        
        first = line
        body = []
        line = (yield None)
        while (line is not None) and (line.strip() != ''):
            body.append(line)
            line = (yield None)
        
        # Output
        magic_name, _, first = first.partition(' ')
        magic_name = magic_name.lstrip(ESC_MAGIC2)
        line = tpl % (magic_name, first, '\n'.join(body))
