import re
from sphinx import addnodes

line_magic_re = re.compile(r"%([\w_]+)")
cell_magic_re = re.compile(r"%%([\w_]+)")

def parse_magic(env, sig, signode):
    m = line_magic_re.match(sig)
    if not m:
        raise Exception("Invalid magic command: %s" % sig)
    signode += addnodes.desc_name(sig, sig)
    return m.group(1)

def parse_cell_magic(env, sig, signode):
    m = cell_magic_re.match(sig)
    if not m:
        raise ValueError("Invalid cell magic: %s" % sig)
    signode += addnodes.desc_name(sig, sig)
    return m.group(1)


def setup(app):    
    app.add_object_type('magic', 'magic', '%%%s (magic command)', parse_magic)
    app.add_object_type('cellmagic', 'cellmagic', '%%%%%s (cell magic)', parse_cell_magic)
