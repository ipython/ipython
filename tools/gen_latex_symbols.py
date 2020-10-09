# coding: utf-8

# This script autogenerates `IPython.core.latex_symbols.py`, which contains a
# single dict , named `latex_symbols`. The keys in this dict are latex symbols,
# such as `\\alpha` and the values in the dict are the unicode equivalents for
# those. Most importantly, only unicode symbols that are valid identifiers in
# Python 3 are included. 

# 
# The original mapping of latex symbols to unicode comes from the `latex_symbols.jl` files from Julia.

from pathlib import Path

# Import the Julia LaTeX symbols
print('Importing latex_symbols.js from Julia...')
import requests
url = 'https://raw.githubusercontent.com/JuliaLang/julia/master/stdlib/REPL/src/latex_symbols.jl'
r = requests.get(url)


# Build a list of key, value pairs
print('Building a list of (latex, unicode) key-value pairs...')
lines = r.text.splitlines()

prefixes_line = lines.index('# "font" prefixes')
symbols_line = lines.index('# manual additions:')

prefix_dict = {}
for l in lines[prefixes_line + 1: symbols_line]:
    p = l.split()
    if not p or p[1] == 'latex_symbols': continue
    prefix_dict[p[1]] = p[3]

idents = []
for l in lines[symbols_line:]:
    if not '=>' in l: continue # if it's not a def, skip
    if '#' in l: l = l[:l.index('#')] # get rid of eol comments
    x, y = l.strip().split('=>') 
    if '*' in x: # if a prefix is present substitute it with its value
        p, x = x.split('*')
        x = prefix_dict[p][:-1] + x[1:]
    x, y = x.split('"')[1], y.split('"')[1] # get the values in quotes
    idents.append((x, y))

# Filter out non-valid identifiers
print('Filtering out characters that are not valid Python 3 identifiers')

def test_ident(i):
    """Is the unicode string valid in a Python 3 identifier."""
    # Some characters are not valid at the start of a name, but we still want to
    # include them. So prefix with 'a', which is valid at the start.
    return ('a' + i).isidentifier()

assert test_ident("α")
assert not test_ident('‴')

valid_idents = [line for line in idents if test_ident(line[1])]

# Write the `latex_symbols.py` module in the cwd

s = """# encoding: utf-8

# DO NOT EDIT THIS FILE BY HAND.

# To update this file, run the script /tools/gen_latex_symbols.py using Python 3

# This file is autogenerated from the file:
# https://raw.githubusercontent.com/JuliaLang/julia/master/base/latex_symbols.jl
# This original list is filtered to remove any unicode characters that are not valid
# Python identifiers.

latex_symbols = {\n
"""
for line in valid_idents:
    s += '    "%s" : "%s",\n' % (line[0], line[1])
s += "}\n"

s += """

reverse_latex_symbol = { v:k for k,v in latex_symbols.items()}
"""

fn = Path('..', 'IPython', 'core', 'latex_symbols.py')
print("Writing the file: %s" % str(fn))
fn.write_text(s, encoding='utf-8')


