#!/usr/bin/env python

from os.path import join, dirname, abspath

from IPython.terminal.ipapp import TerminalIPythonApp
from ipykernel.kernelapp import IPKernelApp
from traitlets import Undefined

here = abspath(dirname(__file__))
options = join(here, 'source', 'config', 'options')
generated = join(options, 'config-generated.txt')

from ipython_genutils.text import indent, dedent

def interesting_default_value(dv):
    if (dv is None) or (dv is Undefined):
        return False
    if isinstance(dv, (str, list, tuple, dict, set)):
        return bool(dv)
    return True

def class_config_rst_doc(cls):
    """Generate rST documentation for this class' config options.

    Excludes traits defined on parent classes.
    """
    lines = []
    classname = cls.__name__
    for k, trait in sorted(cls.class_traits(config=True).items()):
        ttype = trait.__class__.__name__

        lines += ['.. configtrait:: ' + classname + '.' + trait.name,
                  ''
                 ]

        help = trait.help.rstrip() or 'No description'
        lines.append(indent(dedent(help), 4) + '\n')

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

        # Blank line
        lines.append('')

    return '\n'.join(lines)


def write_doc(name, title, app, preamble=None):
    filename = join(options, name+'.rst')
    with open(filename, 'w') as f:
        f.write(title + '\n')
        f.write(('=' * len(title)) + '\n')
        f.write('\n')
        if preamble is not None:
            f.write(preamble + '\n\n')
        #f.write(app.document_config_options())

        for c in app._classes_inc_parents():
            f.write(class_config_rst_doc(c))
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
