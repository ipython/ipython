import abc
import re
from StringIO import StringIO
import tokenize

from IPython.core.splitinput import split_user_input, LineInfo

#-----------------------------------------------------------------------------
# Globals
#-----------------------------------------------------------------------------

# The escape sequences that define the syntax transformations IPython will
# apply to user input.  These can NOT be just changed here: many regular
# expressions and other parts of the code may use their hardcoded values, and
# for all intents and purposes they constitute the 'IPython syntax', so they
# should be considered fixed.

ESC_SHELL  = '!'     # Send line to underlying system shell
ESC_SH_CAP = '!!'    # Send line to system shell and capture output
ESC_HELP   = '?'     # Find information about object
ESC_HELP2  = '??'    # Find extra-detailed information about object
ESC_MAGIC  = '%'     # Call magic function
ESC_MAGIC2 = '%%'    # Call cell-magic function
ESC_QUOTE  = ','     # Split args on whitespace, quote each as string and call
ESC_QUOTE2 = ';'     # Quote all args as a single string, call
ESC_PAREN  = '/'     # Call first argument with rest of line as arguments

ESC_SEQUENCES = [ESC_SHELL, ESC_SH_CAP, ESC_HELP ,\
                 ESC_HELP2, ESC_MAGIC, ESC_MAGIC2,\
                 ESC_QUOTE, ESC_QUOTE2, ESC_PAREN ]


class InputTransformer(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def push(self, line):
        pass
    
    @abc.abstractmethod
    def reset(self):
        pass
    
    look_in_string = False

def stateless_input_transformer(func):
    class StatelessInputTransformer(InputTransformer):
        """Decorator for a stateless input transformer implemented as a function."""
        def __init__(self):
            self.func = func
        
        def push(self, line):
            return self.func(line)
        
        def reset(self):
            pass
    
    return StatelessInputTransformer

def coroutine_input_transformer(coro):
    class CoroutineInputTransformer(InputTransformer):
        def __init__(self):
            # Prime it
            self.coro = coro()
            next(self.coro)
        
        def push(self, line):
            return self.coro.send(line)
        
        def reset(self):
            return self.coro.send(None)
    
    return CoroutineInputTransformer


# Utilities
def _make_help_call(target, esc, lspace, next_input=None):
    """Prepares a pinfo(2)/psearch call from a target name and the escape
    (i.e. ? or ??)"""
    method  = 'pinfo2' if esc == '??' \
                else 'psearch' if '*' in target \
                else 'pinfo'
    arg = " ".join([method, target])
    if next_input is None:
        return '%sget_ipython().magic(%r)' % (lspace, arg)
    else:
        return '%sget_ipython().set_next_input(%r);get_ipython().magic(%r)' % \
           (lspace, next_input, arg)

@coroutine_input_transformer
def escaped_transformer():
    """Translate lines beginning with one of IPython's escape characters."""
    
    # These define the transformations for the different escape characters.
    def _tr_system(line_info):
        "Translate lines escaped with: !"
        cmd = line_info.line.lstrip().lstrip(ESC_SHELL)
        return '%sget_ipython().system(%r)' % (line_info.pre, cmd)

    def _tr_system2(line_info):
        "Translate lines escaped with: !!"
        cmd = line_info.line.lstrip()[2:]
        return '%sget_ipython().getoutput(%r)' % (line_info.pre, cmd)

    def _tr_help(line_info):
        "Translate lines escaped with: ?/??"
        # A naked help line should just fire the intro help screen
        if not line_info.line[1:]:
            return 'get_ipython().show_usage()'

        return _make_help_call(line_info.ifun, line_info.esc, line_info.pre)

    def _tr_magic(line_info):
        "Translate lines escaped with: %"
        tpl = '%sget_ipython().magic(%r)'
        cmd = ' '.join([line_info.ifun, line_info.the_rest]).strip()
        return tpl % (line_info.pre, cmd)

    def _tr_quote(line_info):
        "Translate lines escaped with: ,"
        return '%s%s("%s")' % (line_info.pre, line_info.ifun,
                             '", "'.join(line_info.the_rest.split()) )

    def _tr_quote2(line_info):
        "Translate lines escaped with: ;"
        return '%s%s("%s")' % (line_info.pre, line_info.ifun,
                               line_info.the_rest)

    def _tr_paren(line_info):
        "Translate lines escaped with: /"
        return '%s%s(%s)' % (line_info.pre, line_info.ifun,
                             ", ".join(line_info.the_rest.split()))
    
    tr = { ESC_SHELL  : _tr_system,
           ESC_SH_CAP : _tr_system2,
           ESC_HELP   : _tr_help,
           ESC_HELP2  : _tr_help,
           ESC_MAGIC  : _tr_magic,
           ESC_QUOTE  : _tr_quote,
           ESC_QUOTE2 : _tr_quote2,
           ESC_PAREN  : _tr_paren }
    
    line = ''
    while True:
        line = (yield line)
        if not line or line.isspace():
            continue
        lineinf = LineInfo(line)
        if lineinf.esc not in tr:
            continue
        
        parts = []
        while line is not None:
            parts.append(line.rstrip('\\'))
            if not line.endswith('\\'):
                break
            line = (yield None)
        
        # Output
        lineinf = LineInfo(' '.join(parts))
        line = tr[lineinf.esc](lineinf)

_initial_space_re = re.compile(r'\s*')

_help_end_re = re.compile(r"""(%{0,2}
                              [a-zA-Z_*][\w*]*        # Variable name
                              (\.[a-zA-Z_*][\w*]*)*   # .etc.etc
                              )
                              (\?\??)$                # ? or ??""",
                              re.VERBOSE)

def has_comment(src):
    """Indicate whether an input line has (i.e. ends in, or is) a comment.

    This uses tokenize, so it can distinguish comments from # inside strings.

    Parameters
    ----------
    src : string
      A single line input string.

    Returns
    -------
    Boolean: True if source has a comment.
    """
    readline = StringIO(src).readline
    toktypes = set()
    try:
        for t in tokenize.generate_tokens(readline):
            toktypes.add(t[0])
    except tokenize.TokenError:
        pass
    return(tokenize.COMMENT in toktypes)


@stateless_input_transformer
def help_end(line):
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


@coroutine_input_transformer
def cellmagic():
    tpl = 'get_ipython().run_cell_magic(%r, %r, %r)'
    cellmagic_help_re = re.compile('%%\w+\?')
    line = ''
    while True:
        line = (yield line)
        if (not line) or (not line.startswith(ESC_MAGIC2)):
            continue
        
        if cellmagic_help_re.match(line):
            # This case will be handled by help_end
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
        line = tpl % (magic_name, first, u'\n'.join(body))


def _strip_prompts(prompt1_re, prompt2_re):
    """Remove matching input prompts from a block of input."""
    line = ''
    while True:
        line = (yield line)
        
        if line is None:
            continue
        
        m = prompt1_re.match(line)
        if m:
            while m:
                line = (yield line[len(m.group(0)):])
                if line is None:
                    break
                m = prompt2_re.match(line)
        else:
            # Prompts not in input - wait for reset
            while line is not None:
                line = (yield line)

@coroutine_input_transformer
def classic_prompt():
    prompt1_re = re.compile(r'^(>>> )')
    prompt2_re = re.compile(r'^(>>> |^\.\.\. )')
    return _strip_prompts(prompt1_re, prompt2_re)

classic_prompt.look_in_string = True

@coroutine_input_transformer
def ipy_prompt():
    prompt1_re = re.compile(r'^In \[\d+\]: ')
    prompt2_re = re.compile(r'^(In \[\d+\]: |^\ \ \ \.\.\.+: )')
    return _strip_prompts(prompt1_re, prompt2_re)

ipy_prompt.look_in_string = True


@coroutine_input_transformer
def leading_indent():
    space_re = re.compile(r'^[ \t]+')
    line = ''
    while True:
        line = (yield line)
        
        if line is None:
            continue
        
        m = space_re.match(line)
        if m:
            space = m.group(0)
            while line is not None:
                if line.startswith(space):
                    line = line[len(space):]
                line = (yield line)
        else:
            # No leading spaces - wait for reset
            while line is not None:
                line = (yield line)

leading_indent.look_in_string = True


def _special_assignment(assignment_re, template):
    line = ''
    while True:
        line = (yield line)
        if not line or line.isspace():
            continue
        
        m = assignment_re.match(line)
        if not m:
            continue
        
        parts = []
        while line is not None:
            parts.append(line.rstrip('\\'))
            if not line.endswith('\\'):
                break
            line = (yield None)
        
        # Output
        whole = assignment_re.match(' '.join(parts))
        line = template % (whole.group('lhs'), whole.group('cmd'))

@coroutine_input_transformer
def assign_from_system():
    assignment_re = re.compile(r'(?P<lhs>(\s*)([\w\.]+)((\s*,\s*[\w\.]+)*))'
                               r'\s*=\s*!\s*(?P<cmd>.*)')
    template = '%s = get_ipython().getoutput(%r)'
    return _special_assignment(assignment_re, template)

@coroutine_input_transformer
def assign_from_magic():
    assignment_re = re.compile(r'(?P<lhs>(\s*)([\w\.]+)((\s*,\s*[\w\.]+)*))'
                               r'\s*=\s*%\s*(?P<cmd>.*)')
    template = '%s = get_ipython().magic(%r)'
    return _special_assignment(assignment_re, template)
