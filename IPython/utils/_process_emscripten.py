"""Emscripten-specific implementation of process utilities.

This file is only meant to be imported by process.py, not by end-users.
"""


def system(cmd):
    raise OSError("Not available")


def getoutput(cmd):
    raise OSError("Not available")


def check_pid(cmd):
    raise OSError("Not available")


def arg_split(s, posix=False, strict=True):
    """This one could be made to work but it's not clear if it would be useful..."""
    raise OSError("Not available")
