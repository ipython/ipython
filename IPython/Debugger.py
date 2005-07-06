# -*- coding: utf-8 -*-
"""
Pdb debugger class.

Modified from the standard pdb.Pdb class to avoid including readline, so that
the command line completion of other programs which include this isn't
damaged.

In the future, this class will be expanded with improvements over the standard
pdb.

The code in this file is mainly lifted out of cmd.py in Python 2.2, with minor
changes. Licensing should therefore be under the standard Python terms.  For
details on the PSF (Python Software Foundation) standard license, see:

http://www.python.org/2.2.3/license.html

$Id: Debugger.py 590 2005-05-30 06:26:51Z fperez $"""

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = 'Python'

import pdb,bdb,cmd,os,sys

class Pdb(pdb.Pdb):
    """Modified Pdb class, does not load readline."""
    def __init__(self):
        bdb.Bdb.__init__(self)
        cmd.Cmd.__init__(self,completekey=None) # don't load readline
        self.prompt = '(Pdb) '
        self.aliases = {}

        # Read $HOME/.pdbrc and ./.pdbrc
        self.rcLines = []
        if os.environ.has_key('HOME'):
            envHome = os.environ['HOME']
            try:
                rcFile = open(os.path.join(envHome, ".pdbrc"))
            except IOError:
                pass
            else:
                for line in rcFile.readlines():
                    self.rcLines.append(line)
                rcFile.close()
        try:
            rcFile = open(".pdbrc")
        except IOError:
            pass
        else:
            for line in rcFile.readlines():
                self.rcLines.append(line)
            rcFile.close()
