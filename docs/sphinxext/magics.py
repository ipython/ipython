import re
from sphinx import addnodes
from sphinx.domains.std import StandardDomain
from sphinx.roles import XRefRole

name_re = re.compile(r"[\w_]+")

def parse_magic(env, sig, signode):
    m = name_re.match(sig)
    if not m:
        raise Exception("Invalid magic command: %s" % sig)
    name = "%" + sig
    signode += addnodes.desc_name(name, name)
    return m.group(0)

class LineMagicRole(XRefRole):
    """Cross reference role displayed with a % prefix"""
    prefix = "%"

    def process_link(self, env, refnode, has_explicit_title, title, target):
        if not has_explicit_title:
            title = self.prefix + title.lstrip("%")
        target = target.lstrip("%")
        return title, target

def parse_cell_magic(env, sig, signode):
    m = name_re.match(sig)
    if not m:
        raise ValueError("Invalid cell magic: %s" % sig)
    name = "%%" + sig
    signode += addnodes.desc_name(name, name)
    return m.group(0)

class CellMagicRole(LineMagicRole):
    """Cross reference role displayed with a %% prefix"""
    prefix = "%%"

def setup(app):
    app.add_object_type('magic', 'magic', 'pair: %s; magic command', parse_magic)
    app.add_role_to_domain('std', 'magic', LineMagicRole(), override=True)

    app.add_object_type('cellmagic', 'cellmagic', 'pair: %s; cell magic', parse_cell_magic)
    app.add_role_to_domain('std', 'cellmagic', CellMagicRole(), override=True)

    metadata = {'parallel_read_safe': True, 'parallel_write_safe': True}
    return metadata
