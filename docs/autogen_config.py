from IPython.utils.text import indent, wrap_paragraphs

from IPython.terminal.ipapp import TerminalIPythonApp
from IPython.kernel.zmq.kernelapp import IPKernelApp
from IPython.html.notebookapp import NotebookApp
from IPython.qt.console.qtconsoleapp import IPythonQtConsoleApp

def document_config_options(classes):
    lines = []
    for cls in classes:
        classname = cls.__name__
        for k, trait in sorted(cls.class_traits(config=True).items()):
            ttype = trait.__class__.__name__

            termline = classname + '.' + trait.name

            # Choices or type
            if 'Enum' in ttype:
                # include Enum choices
                termline += ' : ' + '|'.join(repr(x) for x in trait.values)
            else:
                termline += ' : ' + ttype
            lines.append(termline)

            # Default value
            try:
                dv = trait.get_default_value()
                dvr = repr(dv)
            except Exception:
                dvr = dv = None # ignore defaults we can't construct
            if (dv is not None) and (dvr is not None):
                if len(dvr) > 64:
                    dvr = dvr[:61]+'...'
                # Double up backslashes, so they get to the rendered docs
                dvr = dvr.replace('\\n', '\\\\n')
                lines.append('    Default: ' + dvr)
                lines.append('')

            help = trait.get_metadata('help')
            if help is not None:
                help = '\n'.join(wrap_paragraphs(help, 76))
                lines.append(indent(help, 4))
            else:
                lines.append('    No description')

            lines.append('')
    return '\n'.join(lines)

kernel_classes = IPKernelApp().classes

def write_doc(filename, title, classes, preamble=None):
    configdoc = document_config_options(classes)
    with open('source/config/options/%s.rst' % filename, 'w') as f:
        f.write(title + '\n')
        f.write(('=' * len(title)) + '\n')
        f.write('\n')
        if preamble is not None:
            f.write(preamble + '\n\n')
        f.write(configdoc)

if __name__ == '__main__':
    write_doc('terminal', 'Terminal IPython options', TerminalIPythonApp().classes)
    write_doc('kernel', 'IPython kernel options', kernel_classes,
              preamble="These options can be used in :file:`ipython_notebook_config.py` "
              "or in :file:`ipython_qtconsole_config.py`")
    nbclasses = set(NotebookApp().classes) - set(kernel_classes)
    write_doc('notebook', 'IPython notebook options', nbclasses,
              preamble="Any of the :doc:`kernel` can also be used.")
    qtclasses = set(IPythonQtConsoleApp().classes) - set(kernel_classes)
    write_doc('qtconsole', 'IPython Qt console options', qtclasses,
              preamble="Any of the :doc:`kernel` can also be used.")

    with open('source/config/options/generated', 'w'):
        pass