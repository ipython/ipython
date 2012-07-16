import inspect
from IPython.core import ipapi
from IPython.utils.process import arg_split
ip = ipapi.get()

from IPython.core import debugger

def call_pydb(self, args):
    """Invoke pydb with the supplied parameters."""
    try:
        import pydb
    except ImportError:
        raise ImportError("pydb doesn't seem to be installed.")

    if not hasattr(pydb.pydb, "runv"):
        raise ImportError("You need pydb version 1.19 or later installed.")

    argl = arg_split(args)
    # print argl # dbg
    if len(inspect.getargspec(pydb.runv)[0]) == 2:
        pdb = debugger.Pdb(color_scheme=self.colors)
        ip.history_saving_wrapper( lambda : pydb.runv(argl, pdb) )()
    else:
        ip.history_saving_wrapper( lambda : pydb.runv(argl) )()

    
ip.define_magic("pydb",call_pydb)    

    
    
    
