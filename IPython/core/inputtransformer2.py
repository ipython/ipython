import re
from typing import List, Tuple
from IPython.utils import tokenize2
from IPython.utils.tokenutil import generate_tokens

def leading_indent(lines):
    """Remove leading indentation.
    
    If the first line starts with a spaces or tabs, the same whitespace will be
    removed from each following line.
    """
    m = re.match(r'^[ \t]+', lines[0])
    if not m:
        return lines
    space = m.group(0)
    n = len(space)
    return [l[n:] if l.startswith(space) else l
            for l in lines]

class PromptStripper:
    """Remove matching input prompts from a block of input.
    
    Parameters
    ----------
    prompt_re : regular expression
        A regular expression matching any input prompt (including continuation)
    initial_re : regular expression, optional
        A regular expression matching only the initial prompt, but not continuation.
        If no initial expression is given, prompt_re will be used everywhere.
        Used mainly for plain Python prompts, where the continuation prompt
        ``...`` is a valid Python expression in Python 3, so shouldn't be stripped.
    
    If initial_re and prompt_re differ,
    only initial_re will be tested against the first line.
    If any prompt is found on the first two lines,
    prompts will be stripped from the rest of the block.
    """
    def __init__(self, prompt_re, initial_re=None):
        self.prompt_re = prompt_re
        self.initial_re = initial_re or prompt_re

    def _strip(self, lines):
        return [self.prompt_re.sub('', l, count=1) for l in lines]

    def __call__(self, lines):
        if self.initial_re.match(lines[0]) or \
                (len(lines) > 1 and self.prompt_re.match(lines[1])):
            return self._strip(lines)
        return lines

classic_prompt = PromptStripper(
    prompt_re=re.compile(r'^(>>>|\.\.\.)( |$)'),
    initial_re=re.compile(r'^>>>( |$)')
)

ipython_prompt = PromptStripper(re.compile(r'^(In \[\d+\]: |\s*\.{3,}: ?)'))

def cell_magic(lines):
    if not lines[0].startswith('%%'):
        return lines
    if re.match('%%\w+\?', lines[0]):
        # This case will be handled by help_end
        return lines
    magic_name, first_line = lines[0][2:].partition(' ')
    body = '\n'.join(lines[1:])
    return ['get_ipython().run_cell_magic(%r, %r, %r)' % (magic_name, first_line, body)]

line_transforms = [
    leading_indent,
    classic_prompt,
    ipython_prompt,
    cell_magic,
]

# -----

def help_end(tokens_by_line):
    pass

def escaped_command(tokens_by_line):
    pass

def _find_assign_op(token_line):
    # Find the first assignment in the line ('=' not inside brackets)
    # We don't try to support multiple special assignment (a = b = %foo)
    paren_level = 0
    for i, ti in enumerate(token_line):
        s = ti.string
        if s == '=' and paren_level == 0:
            return i 
        if s in '([{':
            paren_level += 1
        elif s in ')]}':
            paren_level -= 1

class MagicAssign:
    @staticmethod
    def find(tokens_by_line):
        """Find the first magic assignment (a = %foo) in the cell.
        
        Returns (line, column) of the % if found, or None.
        """
        for line in tokens_by_line:
            assign_ix = _find_assign_op(line)
            if (assign_ix is not None) \
                    and (len(line) >= assign_ix + 2) \
                    and (line[assign_ix+1].string == '%') \
                    and (line[assign_ix+2].type == tokenize2.NAME):
                return line[assign_ix+1].start
    
    @staticmethod
    def transform(lines: List[str], start: Tuple[int, int]):
        """Transform a magic assignment found by find
        """
        start_line = start[0] - 1   # Shift from 1-index to 0-index
        start_col  = start[1]
        
        print("Start at", start_line, start_col)
        print("Line", lines[start_line])
    
        lhs, rhs = lines[start_line][:start_col], lines[start_line][start_col:-1]
        assert rhs.startswith('%'), rhs
        magic_name, _, args = rhs[1:].partition(' ')
        args_parts = [args]
        end_line = start_line
        # Follow explicit (backslash) line continuations
        while end_line < len(lines) and args_parts[-1].endswith('\\'):
            end_line += 1
            args_parts[-1] = args_parts[-1][:-1]  # Trim backslash
            args_parts.append(lines[end_line][:-1])  # Trim newline
        args = ' '.join(args_parts)
        
        lines_before = lines[:start_line]
        call = "get_ipython().run_line_magic({!r}, {!r})".format(magic_name, args)
        new_line = lhs + call + '\n'
        lines_after = lines[end_line+1:]
        
        return lines_before + [new_line] + lines_after


class SystemAssign:
    @staticmethod
    def find(tokens_by_line):
        """Find the first system assignment (a = !foo) in the cell.

        Returns (line, column) of the ! if found, or None.
        """
        for line in tokens_by_line:
            assign_ix = _find_assign_op(line)
            if (assign_ix is not None) \
                    and (len(line) >= assign_ix + 2) \
                    and (line[assign_ix + 1].type == tokenize2.ERRORTOKEN):
                ix = assign_ix + 1

                while ix < len(line) and line[ix].type == tokenize2.ERRORTOKEN:
                    if line[ix].string == '!':
                        return line[ix].start
                    elif not line[ix].string.isspace():
                        break
                    ix += 1

    @staticmethod
    def transform(lines: List[str], start: Tuple[int, int]):
        """Transform a system assignment found by find
        """
        start_line = start[0] - 1  # Shift from 1-index to 0-index
        start_col = start[1]

        print("Start at", start_line, start_col)
        print("Line", lines[start_line])

        lhs, rhs = lines[start_line][:start_col], lines[start_line][
                                                  start_col:-1]
        assert rhs.startswith('!'), rhs
        cmd_parts = [rhs[1:]]
        end_line = start_line
        # Follow explicit (backslash) line continuations
        while end_line < len(lines) and cmd_parts[-1].endswith('\\'):
            end_line += 1
            cmd_parts[-1] = cmd_parts[-1][:-1]  # Trim backslash
            cmd_parts.append(lines[end_line][:-1])  # Trim newline
        cmd = ' '.join(cmd_parts)

        lines_before = lines[:start_line]
        call = "get_ipython().getoutput({!r})".format(cmd)
        new_line = lhs + call + '\n'
        lines_after = lines[end_line + 1:]

        return lines_before + [new_line] + lines_after

def make_tokens_by_line(lines):
    tokens_by_line = [[]]
    for token in generate_tokens(iter(lines).__next__):
        tokens_by_line[-1].append(token)
        if token.type == tokenize2.NEWLINE:
            tokens_by_line.append([])
    
    return tokens_by_line

class TokenTransformers:
    def __init__(self):
        self.transformers = [
            MagicAssign,
            SystemAssign,
        ]
    
    def do_one_transform(self, lines):
        """Find and run the transform earliest in the code.
        
        Returns (changed, lines).
        
        This method is called repeatedly until changed is False, indicating
        that all available transformations are complete.

        The tokens following IPython special syntax might not be valid, so
        the transformed code is retokenised every time to identify the next
        piece of special syntax. Hopefully long code cells are mostly valid
        Python, not using lots of IPython special syntax, so this shouldn't be
        a performance issue. 
        """
        tokens_by_line = make_tokens_by_line(lines)
        candidates = []
        for transformer in self.transformers:
            locn = transformer.find(tokens_by_line)
            if locn:
                candidates.append((locn, transformer))
        
        if not candidates:
            # Nothing to transform
            return False, lines
        
        first_locn, transformer = min(candidates)
        return True, transformer.transform(lines, first_locn)

    def __call__(self, lines):
        while True:
            changed, lines = self.do_one_transform(lines)
            if not changed:
                return lines

def assign_from_system(tokens_by_line, lines):
    pass


def transform_cell(cell):
    if not cell.endswith('\n'):
        cell += '\n'  # Ensure every line has a newline
    lines = cell.splitlines(keepends=True)
    for transform in line_transforms:
        #print(transform, lines)
        lines = transform(lines)
    
    lines = TokenTransformers()(lines)
    for line in lines:
        print('~~', line)
