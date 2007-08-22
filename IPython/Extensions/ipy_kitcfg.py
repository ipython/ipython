
import os,sys

def selflaunch(line):
    """ Launch python script with 'this' interpreter
    
    e.g. d:\foo\ipython.exe a.py
    
    """
    cmd = sys.executable + ' ' + line.split(None,1)[1]
    print ">",cmd
    os.system(cmd)
    
def main():
    import IPython.ipapi
    ip = IPython.ipapi.get()

    root = os.environ.get('IPYKITROOT', None)
    if not root:
        print "Can't configure ipykit, IPYKITROOT should be set."
        return
    
    os.environ["PATH"] = os.environ["PATH"] + ";" + root + "\\bin;"
    
    ip.defalias('py',selflaunch)
    
    ip.defalias('ls','ls -F')

main()


