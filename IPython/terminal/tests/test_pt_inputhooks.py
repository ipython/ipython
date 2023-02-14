import os
import importlib

import pytest

from IPython.terminal.pt_inputhooks import set_qt_api, get_inputhook_name_and_func


guis_avail = []


def _get_qt_vers():
    """If any version of Qt is available, this will populate `guis_avail` with 'qt' and 'qtx'. Due
    to the import mechanism, we can't import multiple versions of Qt in one session."""
    for gui in ["qt", "qt6", "qt5"]:
        print(f"Trying {gui}")
        try:
            set_qt_api(gui)
            importlib.import_module("IPython.terminal.pt_inputhooks.qt")
            guis_avail.append(gui)
            if "QT_API" in os.environ.keys():
                del os.environ["QT_API"]
        except ImportError:
            pass  # that version of Qt isn't available.
        except RuntimeError:
            pass  # the version of IPython doesn't know what to do with this Qt version.


_get_qt_vers()


@pytest.mark.skipif(
    len(guis_avail) == 0, reason="No viable version of PyQt or PySide installed."
)
def test_inputhook_qt():
    gui = guis_avail[0]

    # Choose a qt version and get the input hook function. This will import Qt...
    get_inputhook_name_and_func(gui)

    # ...and now we're stuck with this version of Qt for good; can't switch.
    for not_gui in ["qt6", "qt5"]:
        if not_gui not in guis_avail:
            break

    with pytest.raises(ImportError):
        get_inputhook_name_and_func(not_gui)

    # A gui of 'qt' means "best available", or in this case, the last one that was used.
    get_inputhook_name_and_func("qt")
