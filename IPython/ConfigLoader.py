# -*- coding: utf-8 -*-
"""Configuration loader

$Id: ConfigLoader.py 1005 2006-01-12 08:39:26Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

import exceptions
import os
from pprint import pprint

from IPython import ultraTB
from IPython.ipstruct import Struct
from IPython.genutils import *

class ConfigLoaderError(exceptions.Exception):
    """Exception for ConfigLoader class."""

    def __init__(self,args=None):
        self.args = args

class ConfigLoader:

    """Configuration file loader capable of handling recursive inclusions and
    with parametrized conflict resolution for multiply found keys."""

    def __init__(self,conflict=None,field_sep=None,reclimit=15):

        """The reclimit parameter controls the number of recursive
        configuration file inclusions. This way we can stop early on (before
        python's own recursion limit is hit) if there is a circular
        inclusion.

        - conflict: dictionary for conflict resolutions (see Struct.merge())

        """
        self.conflict = conflict
        self.field_sep = field_sep
        self.reset(reclimit)
        
    def reset(self,reclimit=15):
        self.reclimit = reclimit
        self.recdepth = 0
        self.included = []
        
    def load(self,fname,convert=None,recurse_key='',incpath = '.',**kw):
        """Load a configuration file, return the resulting Struct.

        Call: load_config(fname,convert=None,conflict=None,recurse_key='')

         - fname: file to load from.
         - convert: dictionary of type conversions (see read_dict())
         - recurse_key: keyword in dictionary to trigger recursive file
         inclusions.
         """

        if self.recdepth > self.reclimit:
            raise ConfigLoaderError, 'maximum recursive inclusion of rcfiles '+\
                  'exceeded: ' + `self.recdepth` + \
                  '.\nMaybe you have a circular chain of inclusions?'
        self.recdepth += 1
        fname = filefind(fname,incpath)
        data = Struct()
        # avoid including the same file more than once
        if fname in self.included:
            return data
        Xinfo = ultraTB.AutoFormattedTB()
        if convert==None and recurse_key : convert = {qwflat:recurse_key}
        # for production, change warn to 0:
        data.merge(read_dict(fname,convert,fs=self.field_sep,strip=1,
                             warn=0,no_empty=0,**kw))
        # keep track of successfully loaded files
        self.included.append(fname)
        if recurse_key in data.keys():
            for incfilename in data[recurse_key]:
                found=0
                try:
                    incfile = filefind(incfilename,incpath)
                except IOError:
                    if os.name in ['nt','dos']:
                        try:
                            # Try again with '.ini' extension
                            incfilename += '.ini'
                            incfile = filefind(incfilename,incpath)
                        except IOError:
                            found = 0
                        else:
                            found = 1
                    else:
                        found = 0
                else:
                    found = 1
                if found:
                    try:
                        data.merge(self.load(incfile,convert,recurse_key,
                                             incpath,**kw),
                                   self.conflict)
                    except:
                        Xinfo()
                        warn('Problem loading included file: '+
                             `incfilename` + '. Ignoring it...')
                else:
                    warn('File `%s` not found. Included by %s' % (incfilename,fname))

        return data

# end ConfigLoader
