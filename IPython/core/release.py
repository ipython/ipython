# -*- coding: utf-8 -*-
"""Release data for the IPython project."""

#-----------------------------------------------------------------------------
#  Copyright (c) 2008-2011, IPython Development Team.
#  Copyright (c) 2001-2007, Fernando Perez <fernando.perez@colorado.edu>
#  Copyright (c) 2001, Janko Hauser <jhauser@zscout.de>
#  Copyright (c) 2001, Nathaniel Gray <n8gray@caltech.edu>
#
#  Distributed under the terms of the Modified BSD License.
#
#  The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

# Name of the package for release purposes.  This is the name which labels
# the tarballs and RPMs made by distutils, so it's best to lowercase it.
name = 'ipython'

# IPython version information.  An empty _version_extra corresponds to a full
# release.  'dev' as a _version_extra string means this is a development
# version
_version_major = 0
_version_minor = 12
_version_micro = ''  # use '' for first of series, number for 1 and above
#_version_extra = 'rc1'
_version_extra = ''  # Uncomment this for full releases

# Construct full version string from these.
_ver = [_version_major, _version_minor]
if _version_micro:
    _ver.append(_version_micro)
if _version_extra:
    _ver.append(_version_extra)

__version__ = '.'.join(map(str, _ver))

version = __version__  # backwards compatibility name

description = "IPython: Productive Interactive Computing"

long_description = \
"""
IPython provides a rich toolkit to help you make the most out of using Python
interactively.  Its main components are:

* Powerful interactive Python shells (terminal- and Qt-based).
* Support for interactive data visualization and use of GUI toolkits.
* Flexible, embeddable interpreters to load into your own projects.
* Tools for high level and interactive parallel computing.

The enhanced interactive Python shells have the following main features:

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
site <http://github.com/ipython>`_.
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

url = 'http://ipython.org'

# This will only be valid for actual releases sent to PyPI, but that's OK since
# those are the ones we want pip/easy_install to be able to find.
download_url = 'http://archive.ipython.org/release/%s' % version

platforms = ['Linux','Mac OSX','Windows XP/2000/NT']

keywords = ['Interactive','Interpreter','Shell','Parallel','Distributed']

classifiers = [
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research'
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.6',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.1',
    'Programming Language :: Python :: 3.2',
    'Topic :: System :: Distributed Computing',
    'Topic :: System :: Shells'
    ]
