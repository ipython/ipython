# coding: utf-8
from IPython.core.splitinput import split_user_input
from IPython.testing import tools as tt
from IPython.utils import py3compat

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
if py3compat.PY3:
    tests.append((u"Pérez Fernando", (u'', u'', u'Pérez', u'Fernando')))
else:
    tests.append((u"Pérez Fernando", (u'', u'', u'P', u'érez Fernando')))

def test_split_user_input():
    return tt.check_pairs(split_user_input, tests)
