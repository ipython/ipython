import pydb
import IPython.ipapi
from IPython.genutils import arg_split
ip = IPython.ipapi.get()

def call_pydb(self, args):
    argl = arg_split(args)
    # print argl # dbg
    if ip.IP.has_readline:
        ip.IP.savehist()
    try:
        pydb.runl(*argl)
    finally:
    
        if ip.IP.has_readline:
            ip.IP.readline.read_history_file(self.shell.histfile)
    
ip.expose_magic("pydb",call_pydb)    

    
    
    