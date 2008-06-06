# encoding: utf-8

"""General utilities for kernel related things."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

import os, types


#-------------------------------------------------------------------------------
# Code
#-------------------------------------------------------------------------------

def tarModule(mod):
    """Makes a tarball (as a string) of a locally imported module.
        
    This method looks at the __file__ attribute of an imported module
    and makes a tarball of the top level of the module.  It then
    reads the tarball into a binary string.  
    
    The method returns the tarball's name and the binary string
    representing the tarball.
    
    Notes:
    
    - It will handle both single module files, as well as packages.
    - The byte code files (\*.pyc) are not deleted.
    - It has not been tested with modules containing extension code, but 
      it should work in most cases.
    - There are cross platform issues. 
     
    """
     
    if not isinstance(mod, types.ModuleType):
        raise TypeError, "Pass an imported module to push_module"
    module_dir, module_file = os.path.split(mod.__file__)
    
    # Figure out what the module is called and where it is
    print "Locating the module..."
    if "__init__.py" in module_file:  # package
        module_name = module_dir.split("/")[-1]
        module_dir = "/".join(module_dir.split("/")[:-1])
        module_file = module_name
    else:                             # Simple module
        module_name = module_file.split(".")[0]
        module_dir = module_dir
    print "Module (%s) found in:\n%s" % (module_name, module_dir)
        
    # Make a tarball of the module in the cwd
    if module_dir:
        os.system('tar -cf %s.tar -C %s %s' % \
            (module_name, module_dir, module_file))
    else:   # must be the cwd
        os.system('tar -cf %s.tar %s' % \
            (module_name, module_file))
    
    # Read the tarball into a binary string        
    tarball_name = module_name + ".tar"
    tar_file = open(tarball_name,'rb')
    fileString = tar_file.read()
    tar_file.close()
    
    # Remove the local copy of the tarball
    #os.system("rm %s" % tarball_name)
    
    return tarball_name, fileString

#from the Python Cookbook:

def curry(f, *curryArgs, **curryKWargs):
    """Curry the function f with curryArgs and curryKWargs."""
    
    def curried(*args, **kwargs):
        dikt = dict(kwargs)
        dikt.update(curryKWargs)
        return f(*(curryArgs+args), **dikt)
    
    return curried

#useful callbacks

def catcher(r):
    pass

def printer(r, msg=''):
    print "%s\n%r" % (msg, r)
    return r


    

