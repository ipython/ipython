try:
    import validate
    if '__docformat__' in validate.__all__ and validate.__version__.split('.') >= ['1', '0', '1']:
        # __docformat__ was removed in 1.0.1 but 
        validate.__all__ = [i for i in validate.__all__ if i != '__docformat__']
    from validate import *
except ImportError:
    from _validate import *
