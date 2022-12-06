import importlib
import os

aliases = {
    'qt4': 'qt',
    'gtk2': 'gtk',
}

backends = [
    "qt",
    "qt4",
    "qt5",
    "qt6",
    "gtk",
    "gtk2",
    "gtk3",
    "gtk4",
    "tk",
    "wx",
    "pyglet",
    "glut",
    "osx",
    "asyncio",
]

registered = {}

def register(name, inputhook):
    """Register the function *inputhook* as an event loop integration."""
    registered[name] = inputhook


class UnknownBackend(KeyError):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return ("No event loop integration for {!r}. "
                "Supported event loops are: {}").format(self.name,
                                    ', '.join(backends + sorted(registered)))


def get_inputhook_name_and_func(gui):
    if gui in registered:
        return gui, registered[gui]

    if gui not in backends:
        raise UnknownBackend(gui)

    if gui in aliases:
        return get_inputhook_name_and_func(aliases[gui])

    gui_mod = gui
    if gui == "qt5":
        os.environ["QT_API"] = "pyqt5"
        gui_mod = "qt"
    elif gui == "qt6":
        # XXX: this locks us into pyqt6 even if pyside6 is installed.
        os.environ["QT_API"] = "pyqt6"
        gui_mod = "qt"

    print(f'{gui_mod=}')
    # Note: `IPython.terminal.pt_inputhooks.qt` imports `IPython.external.qt_for_kernel` and that's
    # where the environment variable locks us into `pyqt6`, despite the fact that it seems `PySide6`
    # is supported.
    mod = importlib.import_module('IPython.terminal.pt_inputhooks.'+gui_mod)
    return gui, mod.inputhook
