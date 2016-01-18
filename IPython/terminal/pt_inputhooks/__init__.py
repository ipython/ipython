import importlib
import os

aliases = {
    'qt4': 'qt',
}

def get_inputhook_func(gui):
    if gui in aliases:
        return get_inputhook_func(aliases[gui])

    if gui == 'qt5':
        os.environ['QT_API'] = 'pyqt5'

    mod = importlib.import_module('IPython.terminal.pt_inputhooks.'+gui)
    return mod.inputhook
