# -*- coding: utf-8 -*-
"""Release data for the IPython project."""

#*****************************************************************************
#       Copyright (C) 2008-2010  The IPython Development Team
#       Copyright (C) 2001-2008 Fernando Perez <fperez@colorado.edu>
#       Copyright (c) 2001 Janko Hauser <jhauser@zscout.de> and Nathaniel Gray
#       <n8gray@caltech.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# Name of the package for release purposes.  This is the name which labels
# the tarballs and RPMs made by distutils, so it's best to lowercase it.
name = 'ipython'

# For versions with substrings (like 0.6.16.svn), use an extra . to separate
# the new substring.  We have to avoid using either dashes or underscores,
# because bdist_rpm does not accept dashes (an RPM) convention, and
# bdist_deb does not accept underscores (a Debian convention).

development = True    # change this to False to do a release
version_base = '0.10.2'
extra_ver = None  # Default
extra_ver = 'rc1'  # Use for release candidates and similar

if development:
    if extra_ver == None:
        version = '%s.git' % (version_base)
    else:
        version = '%s.%s' % (version_base, extra_ver)
else:
    version = version_base


description = "An interactive computing environment for Python"

long_description = \
"""
The goal of IPython is to create a comprehensive environment for
interactive and exploratory computing.  To support this goal, IPython
has two main components:

* An enhanced interactive Python shell.

* An architecture for interactive parallel computing.

The enhanced interactive Python shell has the following main features:

* Comprehensive object introspection.

* Input history, persistent across sessions.

* Caching of output results during a session with automatically generated
  references.

* Readline based name completion.

* Extensible system of 'magic' commands for controlling the environment and
  performing many tasks related either to IPython or the operating system.

* Configuration system with easy switching between different setups (simpler
  than changing $PYTHONSTARTUP environment variables every time).

* Session logging and reloading.

* Extensible syntax processing for special purpose situations.

* Access to the system shell with user-extensible alias system.

* Easily embeddable in other Python programs and wxPython GUIs.

* Integrated access to the pdb debugger and the Python profiler. 

The parallel computing architecture has the following main features:

* Quickly parallelize Python code from an interactive Python/IPython session.

* A flexible and dynamic process model that be deployed on anything from 
  multicore workstations to supercomputers.

* An architecture that supports many different styles of parallelism, from
  message passing to task farming.

* Both blocking and fully asynchronous interfaces.

* High level APIs that enable many things to be parallelized in a few lines
  of code.

* Share live parallel jobs with other users securely.  

* Dynamically load balanced task farming system.

* Robust error handling in parallel code.

The latest development version is always available from IPython's `GitHub 
site <http://github.com/ipython/ipython>`_.
"""

license = 'BSD'

authors = {'Fernando' : ('Fernando Perez','fperez.net@gmail.com'),
           'Janko'    : ('Janko Hauser','jhauser@zscout.de'),
           'Nathan'   : ('Nathaniel Gray','n8gray@caltech.edu'),
           'Ville'    : ('Ville Vainio','vivainio@gmail.com'),
           'Brian'    : ('Brian E Granger', 'ellisonbg@gmail.com'),
           'Min'      : ('Min Ragan-Kelley', 'benjaminrk@gmail.com')
           }

author = 'The IPython Development Team'

author_email = 'ipython-dev@scipy.org'

url = 'http://ipython.scipy.org'

download_url = 'http://ipython.scipy.org/dist'

platforms = ['Linux','Mac OSX','Windows XP/2000/NT','Windows 95/98/ME']

keywords = ['Interactive','Interpreter','Shell','Parallel','Distributed']
