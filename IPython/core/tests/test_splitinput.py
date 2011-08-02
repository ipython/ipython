from IPython.core.splitinput import split_user_input
from IPython.testing import tools as tt

tests = [
    ('x=1', ('', '', 'x', '=1')),
    ('?', ('', '?', '', '')),
    ('??', ('', '??', '', '')),
    (' ?', (' ', '?', '', '')),
    (' ??', (' ', '??', '', '')),
    ('??x', ('', '??', 'x', '')),
    ('?x=1', ('', '?', 'x', '=1')),
    ('!ls', ('', '!', 'ls', '')),
    ('  !ls', ('  ', '!', 'ls', '')),
    ('!!ls', ('', '!!', 'ls', '')),
    ('  !!ls', ('  ', '!!', 'ls', '')),
    (',ls', ('', ',', 'ls', '')),
    (';ls', ('', ';', 'ls', '')),
    ('  ;ls', ('  ', ';', 'ls', '')),
    ('f.g(x)',  ('', '', 'f.g', '(x)')),
    ('f.g (x)', ('', '', 'f.g', '(x)')),
    ('?%hist', ('', '?', '%hist', '')),
    ('?x*', ('', '?', 'x*', '')),
    ]

def test_split_user_input():
    return tt.check_pairs(split_user_input, tests)
