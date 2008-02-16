import os,sys

import ipy_rehashdir,glob
from ipy_rehashdir import selflaunch, PyLauncher

def pylaunchers():
    """Create launchers for python scripts in cwd and store them in alias table
    
    This is useful if you want to invoke .py scripts from ipykit session,
    just adding .py files in PATH does not work without file association.
    
    .ipy files will be run like macros.
    
    """
    fs = glob.glob('*.py') + glob.glob('*.ipy')
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
  
def kitroot():
    return os.environ.get('IPYKITROOT', None)
    
def main():

    if not kitroot():
        print "Can't configure ipykit, IPYKITROOT should be set."
        return
        
    os.environ["PATH"] = os.environ["PATH"] + ";" + kitroot() + "\\bin;"
    ip.to_user_ns("pylaunchers")
    cmds = ip.db.get('syscmdlist', None)
    if cmds is None:
        ip.magic('rehashx')
        cmds = ip.db.get('syscmdlist', [])
    #print cmds
    if 'sc1' in cmds:
        print "Default editor: Sc1"
        import ipy_editors
        ipy_editors.scite('sc1')
    
    # for icp, imv, imkdir, etc.
    import ipy_fsops

greeting = """\n\n === Welcome to ipykit ===

%quickref - learn quickly about IPython.

"""
    
def ipython_firstrun(ip):

    print "First run of ipykit - configuring"

    ip.defalias('py',selflaunch)
    ip.defalias('d','dir /w /og /on')
    ip.magic('store py')
    ip.magic('store d')
    
    bins = kitroot() +'/bin'

    print greeting
        
def init_ipython(ipy):
    global ip
    ip = ipy
    main()


