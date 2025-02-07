from datetime import datetime
from random import choice
from typing import Any

_tips: Any = {
    # (month, day)
    "every_year": {
        (1, 1): "Happy new year!",
        # https://mail.python.org/pipermail/python-list/2001-December/093408.html
        (12, 9): "IPython was created {} years ago".format(datetime.now().year - 2001),
    },
    "random": [
        "Use F2 or %edit with no arguments to open an empty editor with a temporary file.",
        "Run your doctests from within IPython for development and debugging. The special %doctest_mode command toggles a mode where the prompt, output and exceptions display matches as closely as possible that of the default Python interpreter.",
        "You can use `files = !ls *.png`",
        "Use the IPython.lib.demo.Demo class to load any Python script as an interactive demo.",
        "Put a ‘;’ at the end of a line to suppress the printing of output.",   
        "You can use Ctrl-O to force a new line in terminal IPython",
        "Use `object?` to see the help on `object`, `object??` to view it's source",
        "`?` alone on a line will brings up IPython's help",
        "You can use `%hist` to view history, the the options with `%history?`",
    ],
}


def pick_tip() -> str:
    current_date = datetime.now()
    month, day = current_date.month, current_date.day

    if (month, day) in _tips["every_year"]:
        return _tips["every_year"][(month, day)]

    return choice(_tips["random"])
