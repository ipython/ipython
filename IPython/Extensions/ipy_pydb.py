import pydb
import IPython.ipapi
from IPython.genutils import arg_split
ip = IPython.ipapi.get()

def call_pydb(self, args):
    argl = arg_split(args)
    # print argl # dbg
    ip.IP.history_saving_wrapper( lambda : pydb.runl(*argl) )()
    
ip.expose_magic("pydb",call_pydb)    

    
    
    