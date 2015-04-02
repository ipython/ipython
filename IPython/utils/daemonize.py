from warnings import warn

warn("IPython.utils.daemonize has moved to ipython_parallel.apps.daemonize")
from ipython_parallel.apps.daemonize import daemonize
