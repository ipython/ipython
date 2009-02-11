# encoding: utf-8

"""This is the official entry point to IPython's configuration system.  """

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

import os
from os.path import join as pjoin

from IPython.genutils import get_home_dir, get_ipython_dir
from IPython.external.configobj import ConfigObj


class ConfigObjManager(object):
    
    def __init__(self, configObj, filename):
        self.current = configObj
        self.current.indent_type = '    '
        self.filename = filename
        # self.write_default_config_file()
        
    def get_config_obj(self):
        return self.current
    
    def update_config_obj(self, newConfig):
        self.current.merge(newConfig)
        
    def update_config_obj_from_file(self, filename):
        newConfig = ConfigObj(filename, file_error=False)
        self.current.merge(newConfig)
        
    def update_config_obj_from_default_file(self, ipythondir=None):
        fname = self.resolve_file_path(self.filename, ipythondir)
        self.update_config_obj_from_file(fname)

    def write_config_obj_to_file(self, filename):
        f = open(filename, 'w')
        self.current.write(f)
        f.close()

    def write_default_config_file(self):
        ipdir = get_ipython_dir()
        fname = pjoin(ipdir, self.filename)
        if not os.path.isfile(fname):
            print "Writing the configuration file to: " + fname
            self.write_config_obj_to_file(fname)
    
    def _import(self, key):
        package = '.'.join(key.split('.')[0:-1])
        obj = key.split('.')[-1]
        execString = 'from %s import %s' % (package, obj)
        exec execString
        exec 'temp = %s' % obj 
        return temp

    def resolve_file_path(self, filename, ipythondir = None):
        """Resolve filenames into absolute paths.

        This function looks in the following directories in order:

        1.  In the current working directory or by absolute path with ~ expanded
        2.  In ipythondir if that is set
        3.  In the IPYTHONDIR environment variable if it exists
        4.  In the ~/.ipython directory

        Note: The IPYTHONDIR is also used by the trunk version of IPython so
               changing it will also affect it was well.
        """

        # In cwd or by absolute path with ~ expanded
        trythis = os.path.expanduser(filename)
        if os.path.isfile(trythis):
            return trythis

        # In ipythondir if it is set
        if ipythondir is not None:
            trythis = pjoin(ipythondir, filename)
            if os.path.isfile(trythis):
                return trythis        

        trythis = pjoin(get_ipython_dir(), filename)
        if os.path.isfile(trythis):
            return trythis

        return None


    
    

    
