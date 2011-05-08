try:
    from decorator import *
    from decorator import getinfo, new_wrapper
    # the following funcion is deprecated so using the python own one
    from functools import update_wrapper
except ImportError:
    from _decorator import *
    from _decorator import getinfo, update_wrapper, new_wrapper
