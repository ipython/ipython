try:
    import stack_data
except ImportError:
    from .ultratb_old import *
else:
    from .ultratb_new import *
