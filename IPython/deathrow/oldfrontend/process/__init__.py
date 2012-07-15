"""
Package for dealing for process execution in a callback environment, in a
portable way.

killable_process.py is a wrapper of subprocess.Popen that allows the
subprocess and its children to be killed in a reliable way, including
under windows.

winprocess.py is required by killable_process.py to kill processes under
windows.

piped_process.py wraps process execution with callbacks to print output,
in a non-blocking way. It can be used to interact with a subprocess in eg
a GUI event loop.
"""

from pipedprocess import PipedProcess


