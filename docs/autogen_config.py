#!/usr/bin/env python

from os.path import join, dirname, abspath
import inspect

from IPython.terminal.ipapp import TerminalIPythonApp
from ipykernel.kernelapp import IPKernelApp
from traitlets import Undefined
from collections import defaultdict

here = abspath(dirname(__file__))
options = join(here, 'source', 'config', 'options')
generated = join(options, 'config-generated.txt')

import textwrap
indent = lambda text,n: textwrap.indent(text,n*' ')


def interesting_default_value(dv):
    if (dv is None) or (dv is Undefined):
        return False
    if isinstance(dv, (str, list, tuple, dict, set)):
        return bool(dv)
    return True

def format_aliases(aliases):
    fmted = []
    for a in aliases:
        dashes = '-' if len(a) == 1 else '--'
        fmted.append('``%s%s``' % (dashes, a))
    return ', '.join(fmted)

def class_config_rst_doc(cls, trait_aliases):
    """Generate rST documentation for this class' config options.

    Excludes traits defined on parent classes.
    """
    lines = []
    classname = cls.__name__
    for k, trait in sorted(cls.class_traits(config=True).items()):
        ttype = trait.__class__.__name__

        fullname = classname + '.' + trait.name
        lines += ['.. configtrait:: ' + fullname,
                  ''
                 ]

        help = trait.help.rstrip() or 'No description'
        lines.append(indent(inspect.cleandoc(help), 4) + '\n')

        # Choices or type
        if 'Enum' in ttype:
            # include Enum choices
            lines.append(indent(
                ':options: ' + ', '.join('``%r``' % x for x in trait.values), 4))
        else:
            lines.append(indent(':trait type: ' + ttype, 4))

        # Default value
        # Ignore boring default values like None, [] or ''
        if interesting_default_value(trait.default_value):
            try:
                dvr = trait.default_value_repr()
            except Exception:
                dvr = None  # ignore defaults we can't construct
            if dvr is not None:
                if len(dvr) > 64:
                    dvr = dvr[:61] + '...'
                # Double up backslashes, so they get to the rendered docs
                dvr = dvr.replace('\\n', '\\\\n')
                lines.append(indent(':default: ``%s``' % dvr, 4))

        # Command line aliases
        if trait_aliases[fullname]:
            fmt_aliases = format_aliases(trait_aliases[fullname])
            lines.append(indent(':CLI option: ' + fmt_aliases, 4))

        # Blank line
        lines.append('')

    return '\n'.join(lines)

def reverse_aliases(app):
    """Produce a mapping of trait names to lists of command line aliases.
    """
    res = defaultdict(list)
    for alias, trait in app.aliases.items():
        res[trait].append(alias)

    # Flags also often act as aliases for a boolean trait.
    # Treat flags which set one trait to True as aliases.
    for flag, (cfg, _) in app.flags.items():
        if len(cfg) == 1:
            classname = list(cfg)[0]
            cls_cfg = cfg[classname]
            if len(cls_cfg) == 1:
                traitname = list(cls_cfg)[0]
                if cls_cfg[traitname] is True:
                    res[classname+'.'+traitname].append(flag)

    return res

def write_doc(name, title, app, preamble=None):
    trait_aliases = reverse_aliases(app)
    filename = join(options, name+'.rst')
    with open(filename, 'w') as f:
        f.write(title + '\n')
        f.write(('=' * len(title)) + '\n')
        f.write('\n')
        if preamble is not None:
            f.write(preamble + '\n\n')
        #f.write(app.document_config_options())

        for c in app._classes_inc_parents():
            f.write(class_config_rst_doc(c, trait_aliases))
            f.write('\n')


if __name__ == '__main__':
    # Touch this file for the make target
    with open(generated, 'w'):
        pass

    write_doc('terminal', 'Terminal IPython options', TerminalIPythonApp())
    write_doc('kernel', 'IPython kernel options', IPKernelApp(),
        preamble=("These options can be used in :file:`ipython_kernel_config.py`. "
                  "The kernel also respects any options in `ipython_config.py`"),
    )
