import inspect
import IPython.ipapi
from IPython.genutils import arg_split
ip = IPython.ipapi.get()

from IPython import Debugger

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
        pdb = Debugger.Pdb(color_scheme=self.rc.colors)
        ip.IP.history_saving_wrapper( lambda : pydb.runv(argl, pdb) )()
    else:
        ip.IP.history_saving_wrapper( lambda : pydb.runv(argl) )()

    
ip.expose_magic("pydb",call_pydb)    

    
    
    
