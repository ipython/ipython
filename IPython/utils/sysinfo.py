# encoding: utf-8
"""
Utilities for getting information about a system.
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os
import platform
import sys
import subprocess

from IPython.core import release

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------

def sys_info():
    """Return useful information about IPython and the system, as a string.

    Examples
    --------
    In [1]: print(sys_info())
    IPython version: 0.11.bzr.r1340   # random
    BZR revision   : 1340
    Platform info  : os.name -> posix, sys.platform -> linux2
                   : Linux-2.6.31-17-generic-i686-with-Ubuntu-9.10-karmic
    Python info    : 2.6.4 (r264:75706, Dec  7 2009, 18:45:15) 
    [GCC 4.4.1]
    """
    out = []
    out.append('IPython version: %s' % release.version)
    out.append('BZR revision   : %s' % release.revision)
    out.append('Platform info  : os.name -> %s, sys.platform -> %s' %
               (os.name,sys.platform) )
    out.append('               : %s' % platform.platform())
    out.append('Python info    : %s' % sys.version)
    out.append('')  # ensure closing newline
    return '\n'.join(out)


def _num_cpus_unix():
    """Return the number of active CPUs on a Unix system."""
    return os.sysconf("SC_NPROCESSORS_ONLN")


def _num_cpus_darwin():
    """Return the number of active CPUs on a Darwin system."""
    p = subprocess.Popen(['sysctl','-n','hw.ncpu'],stdout=subprocess.PIPE)
    return p.stdout.read()


def _num_cpus_windows():
    """Return the number of active CPUs on a Windows system."""
    return os.environ.get("NUMBER_OF_PROCESSORS")


def num_cpus():
   """Return the effective number of CPUs in the system as an integer.

   This cross-platform function makes an attempt at finding the total number of
   available CPUs in the system, as returned by various underlying system and
   python calls.

   If it can't find a sensible answer, it returns 1 (though an error *may* make
   it return a large positive number that's actually incorrect).
   """

   # Many thanks to the Parallel Python project (http://www.parallelpython.com)
   # for the names of the keys we needed to look up for this function.  This
   # code was inspired by their equivalent function.

   ncpufuncs = {'Linux':_num_cpus_unix,
                'Darwin':_num_cpus_darwin,
                'Windows':_num_cpus_windows,
                # On Vista, python < 2.5.2 has a bug and returns 'Microsoft'
                # See http://bugs.python.org/issue1082 for details.
                'Microsoft':_num_cpus_windows,
                }

   ncpufunc = ncpufuncs.get(platform.system(),
                            # default to unix version (Solaris, AIX, etc)
                            _num_cpus_unix)

   try:
       ncpus = max(1,int(ncpufunc()))
   except:
       ncpus = 1
   return ncpus

