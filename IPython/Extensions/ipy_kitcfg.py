import os,sys

import ipy_rehashdir,glob
from ipy_rehashdir import selflaunch, PyLauncher

def pylaunchers():
    """Create launchers for python scripts in cwd and store them in alias table
    
    This is useful if you want to invoke .py scripts from ipykit session,
    just adding .py files in PATH does not work without file association.
    
    .ipy files will be run like macros.
    
    """
    fs = glob.glob('*.?py*')
    for f in fs:
        l = PyLauncher(f)
        n = os.path.splitext(f)[0]
        ip.defalias(n, l)
        ip.magic('store '+n)


def exta_imports():
    # add some modules that you'd want to be bundled in the ipykit
    # library zip file here. Do this if you get ImportErrors from scripts you
    # try to launch with 'py' or pylaunchers. In theory you could include
    # the whole stdlib here for full script coverage
    
    # note that this is never run, it's just here for py2exe
    import distutils.dir_util
  
def main():
    root = os.environ.get('IPYKITROOT', None)
    if not root:
        print "Can't configure ipykit, IPYKITROOT should be set."
        return
    
    os.environ["PATH"] = os.environ["PATH"] + ";" + root + "\\bin;"
    ip.to_user_ns("pylaunchers")
    
    
def ipython_firstrun(ip):
    print "First run of ipykit - configuring"
    ip.defalias('py',selflaunch)
    ip.defalias('d','ls -F')
    ip.defalias('ls','ls')
    ip.magic('store py')
    ip.magic('store d')
    ip.magic('store ls')

def init_ipython(ipy):
    global ip
    ip = ipy
    main()


