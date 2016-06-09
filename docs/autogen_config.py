#!/usr/bin/env python

from os.path import join, dirname, abspath

from IPython.terminal.ipapp import TerminalIPythonApp
from ipykernel.kernelapp import IPKernelApp

here = abspath(dirname(__file__))
options = join(here, 'source', 'config', 'options')
generated = join(options, 'config-generated.txt')


def write_doc(name, title, app, preamble=None):
    with open(generated, 'a') as f:
        f.write(title + '\n')
        f.write(('=' * len(title)) + '\n')
        f.write('\n')
        if preamble is not None:
            f.write(preamble + '\n\n')
        f.write(app.document_config_options())


if __name__ == '__main__':
    # create empty file
    with open(generated, 'w'):
        pass

    write_doc('terminal', 'Terminal IPython options', TerminalIPythonApp())
    write_doc('kernel', 'IPython kernel options', IPKernelApp(),
        preamble=("These options can be used in :file:`ipython_kernel_config.py`. "
                  "The kernel also respects any options in `ipython_config.py`"),
    )
