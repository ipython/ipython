# -*- coding: utf-8 -*-
"""
Logger class for IPython's logging facilities.

$Id: Logger.py 430 2004-11-30 08:52:05Z fperez $
"""

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#       Copyright (C) 2001-2004 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

#****************************************************************************
# Modules and globals

from IPython import Release
__author__  = '%s <%s>\n%s <%s>' % \
              ( Release.authors['Janko'] + Release.authors['Fernando'] )
__license__ = Release.license

# Python standard modules
import os,sys,glob

# Homebrewed
from IPython.genutils import *

#****************************************************************************
# FIXME: The logger class shouldn't be a mixin, it throws too many things into
# the InteractiveShell namespace. Rather make it a standalone tool, and create
# a Logger instance in InteractiveShell that uses it. Doing this will require
# tracking down a *lot* of nasty uses of the Logger attributes in
# InteractiveShell, but will clean up things quite a bit.

class Logger:
    """A Logfile Mixin class with different policies for file creation"""

    # FIXME: once this isn't a mixin, log_ns should just be 'namespace', since the
    # names won't collide anymore.
    def __init__(self,log_ns):
        self._i00,self._i,self._ii,self._iii = '','','',''
        self.do_full_cache = 0 # FIXME. There's also a do_full.. in OutputCache
        self.log_ns = log_ns
        # defaults
        self.LOGMODE = 'backup'
        self.defname = 'logfile'
        
    def create_log(self,header='',fname='',defname='.Logger.log'):
        """Generate a new log-file with a default header"""
        if fname:
            self.LOG = fname

        if self.LOG:
            self.logfname = self.LOG
        else:
            self.logfname = defname
        
        if self.LOGMODE == 'over':
            if os.path.isfile(self.logfname):
                os.remove(self.logfname) 
            self.logfile = open(self.logfname,'w')
        if self.LOGMODE == 'backup':
            if os.path.isfile(self.logfname):
                backup_logname = self.logfname+'~'
                # Manually remove any old backup, since os.rename may fail
                # under Windows.
                if os.path.isfile(backup_logname):
                    os.remove(backup_logname)
                os.rename(self.logfname,backup_logname)
            self.logfile = open(self.logfname,'w')
        elif self.LOGMODE == 'global':
            self.logfname = os.path.join(self.home_dir, self.defname)
            self.logfile = open(self.logfname, 'a')
            self.LOG = self.logfname
        elif self.LOGMODE == 'rotate':
            if os.path.isfile(self.logfname):
                if os.path.isfile(self.logfname+'.001~'): 
                    old = glob.glob(self.logfname+'.*~')
                    old.sort()
                    old.reverse()
                    for f in old:
                        root, ext = os.path.splitext(f)
                        num = int(ext[1:-1])+1
                        os.rename(f, root+'.'+`num`.zfill(3)+'~')
                os.rename(self.logfname, self.logfname+'.001~')
            self.logfile = open(self.logfname,'w')
        elif self.LOGMODE == 'append':
            self.logfile = open(self.logfname,'a')
            
        if self.LOGMODE != 'append':
            self.logfile.write(header)
        self.logfile.flush()

    def logstart(self, header='',parameter_s = ''):
        if not hasattr(self, 'LOG'):
            logfname = self.LOG or parameter_s or './'+self.defname
            self.create_log(header,logfname)
        elif parameter_s and hasattr(self,'logfname') and \
             parameter_s != self.logfname:
            self.close_log()
            self.create_log(header,parameter_s)
            
        self._dolog = 1

    def switch_log(self,val):
        """Switch logging on/off. val should be ONLY 0 or 1."""

        if not val in [0,1]:
            raise ValueError, \
                  'Call switch_log ONLY with 0 or 1 as argument, not with:',val
        
        label = {0:'OFF',1:'ON'}

        try:
            _ = self.logfile
        except AttributeError:
            print """
Logging hasn't been started yet (use %logstart for that).

%logon/%logoff are for temporarily starting and stopping logging for a logfile
which already exists. But you must first start the logging process with
%logstart (optionally giving a logfile name)."""
            
        else:
            if self._dolog == val:
                print 'Logging is already',label[val]
            else:
                print 'Switching logging',label[val]
                self._dolog = 1 - self._dolog

    def logstate(self):
        """Print a status message about the logger."""
        try:
            logfile = self.logfname
        except:
            print 'Logging has not been activated.'
        else:
            state = self._dolog and 'active' or 'temporarily suspended'
            print """
File:\t%s
Mode:\t%s
State:\t%s """ % (logfile,self.LOGMODE,state)

        
    def log(self, line,continuation=None):
        """Write the line to a log and create input cache variables _i*."""

        # update the auto _i tables
        #print '***logging line',line # dbg
        #print '***cache_count', self.outputcache.prompt_count # dbg
        input_hist = self.log_ns['_ih']
        if not continuation and line:
            self._iii = self._ii
            self._ii = self._i
            self._i = self._i00
            # put back the final \n of every input line
            self._i00 = line+'\n'
            #print 'Logging input:<%s>' % line  # dbg
            input_hist.append(self._i00)

        # hackish access to top-level namespace to create _i1,_i2... dynamically
        to_main = {'_i':self._i,'_ii':self._ii,'_iii':self._iii}
        if self.do_full_cache:
            in_num = self.outputcache.prompt_count
            # add blank lines if the input cache fell out of sync. This can happen
            # for embedded instances which get killed via C-D and then get resumed.
            while in_num >= len(input_hist):
                input_hist.append('\n')
            new_i = '_i%s' % in_num
            if continuation:
                self._i00 = '%s%s\n' % (self.log_ns[new_i],line)
                input_hist[in_num] = self._i00
            to_main[new_i] = self._i00
        self.log_ns.update(to_main)
        
        if self._dolog and line:
            self.logfile.write(line+'\n')
            self.logfile.flush()

    def close_log(self):
        if hasattr(self, 'logfile'):
            self.logfile.close()
            self.logfname = ''
