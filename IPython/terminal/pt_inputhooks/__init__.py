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


last_qt_version = None  # stores which version (i.e. `gui`) was requested the first time.

def set_qt_api(gui):
    """Sets the `QT_API` environment variable if it isn't already set."""

    global last_qt_version

    if gui != "qt" and last_qt_version is not None:
        if last_qt_version != gui:
            raise ValueError(
                "Cannot switch Qt versions for this session; "
                f"must use {last_qt_version}."
            )

    qt_api = os.environ.get("QT_API", None)
    if qt_api is not None and gui != "qt":
        env2gui = {
            "pyside": "qt4",
            "pyqt": "qt4",
            "pyside2": "qt5",
            "pyqt5": "qt5",
            "pyside6": "qt6",
            "pyqt6": "qt6",
        }
        if env2gui[qt_api] != gui:
            print(
                f'Request for "{gui}" will be ignored because `QT_API` '
                f'environment variable is set to "{qt_api}"'
            )
    else:
        if gui == "qt4":
            try:
                import PyQt  # noqa

                os.environ["QT_API"] = "pyqt"
            except ImportError:
                try:
                    import PySide  # noqa

                    os.environ["QT_API"] = "pyside"
                except ImportError:
                    # Neither implementation installed; set it to something so IPython gives an error
                    os.environ["QT_API"] = "pyqt"
        elif gui == "qt5":
            try:
                import PyQt5  # noqa

                os.environ["QT_API"] = "pyqt5"
            except ImportError:
                try:
                    import PySide2  # noqa

                    os.environ["QT_API"] = "pyside2"
                except ImportError:
                    os.environ["QT_API"] = "pyqt5"
        elif gui == "qt6":
            try:
                import PyQt6  # noqa

                os.environ["QT_API"] = "pyqt6"
            except ImportError:
                try:
                    import PySide6  # noqa

                    os.environ["QT_API"] = "pyside6"
                except ImportError:
                    os.environ["QT_API"] = "pyqt6"
        elif gui == "qt":
            # Don't set QT_API; let IPython logic choose the version.
            if "QT_API" in os.environ.keys():
                del os.environ["QT_API"]
        else:
            raise ValueError(
                f'Unrecognized Qt version: {gui}. Should be "qt4", "qt5", "qt6", or "qt".'
            )

    # Due to the import mechanism, we can't change Qt versions once we've chosen one. So we tag the
    # version so we can check for this and give an error.
    last_qt_version = gui

def get_inputhook_name_and_func(gui):
    print(f'`get_inputhook_name_and_func` called with {gui=}')
    if gui in registered:
        return gui, registered[gui]

    if gui not in backends:
        raise UnknownBackend(gui)

    if gui in aliases:
        print('gui has an alias')
        return get_inputhook_name_and_func(aliases[gui])

    gui_mod = gui
    if gui.startswith("qt"):
        set_qt_api(gui)
        gui_mod = "qt"

    mod = importlib.import_module("IPython.terminal.pt_inputhooks." + gui_mod)
    return gui, mod.inputhook
