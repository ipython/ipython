# -*- coding: utf-8 -*-
"""Release data for the IPython project.

$Id: Release.py 3002 2008-02-01 07:17:00Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
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

revision = '128'
branch = 'ipython'

if branch == 'ipython':
    version = '0.8.4.bzr.r' + revision
else:
    version = '0.8.4.bzr.r%s.%s'  % (revision,branch)

version = '0.8.4'

description = "An enhanced interactive Python shell."

long_description = \
"""
IPython provides a replacement for the interactive Python interpreter with
extra functionality.

Main features:

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

 * Easily embeddable in other Python programs.

 * Integrated access to the pdb debugger and the Python profiler. 

 The latest development version is always available at the IPython subversion
 repository_.

.. _repository: http://ipython.scipy.org/svn/ipython/ipython/trunk#egg=ipython-dev
 """

license = 'BSD'

authors = {'Fernando' : ('Fernando Perez','fperez@colorado.edu'),
           'Janko'    : ('Janko Hauser','jhauser@zscout.de'),
           'Nathan'   : ('Nathaniel Gray','n8gray@caltech.edu'),
           'Ville'    : ('Ville Vainio','vivainio@gmail.com')           
           }

url = 'http://ipython.scipy.org'

download_url = 'http://ipython.scipy.org/dist'

platforms = ['Linux','Mac OSX','Windows XP/2000/NT','Windows 95/98/ME']

keywords = ['Interactive','Interpreter','Shell']
