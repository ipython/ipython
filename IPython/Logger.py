# -*- coding: utf-8 -*-
"""
Logger class for IPython's logging facilities.

$Id: Logger.py 994 2006-01-08 08:29:44Z fperez $
"""

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
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
import glob
import os
import time

#****************************************************************************
# FIXME: This class isn't a mixin anymore, but it still needs attributes from
# ipython and does input cache management.  Finish cleanup later...

class Logger(object):
    """A Logfile class with different policies for file creation"""

    def __init__(self,shell,logfname='Logger.log',loghead='',logmode='over'):

        self._i00,self._i,self._ii,self._iii = '','','',''

        # this is the full ipython instance, we need some attributes from it
        # which won't exist until later. What a mess, clean up later...
        self.shell = shell

        self.logfname = logfname
        self.loghead = loghead
        self.logmode = logmode
        self.logfile = None

        # whether to also log output
        self.log_output = False

        # whether to put timestamps before each log entry
        self.timestamp = False

        # activity control flags
        self.log_active = False

    # logmode is a validated property
    def _set_mode(self,mode):
        if mode not in ['append','backup','global','over','rotate']:
            raise ValueError,'invalid log mode %s given' % mode
        self._logmode = mode

    def _get_mode(self):
        return self._logmode

    logmode = property(_get_mode,_set_mode)
    
    def logstart(self,logfname=None,loghead=None,logmode=None,
                 log_output=False,timestamp=False):
        """Generate a new log-file with a default header.

        Raises RuntimeError if the log has already been started"""

        if self.logfile is not None:
            raise RuntimeError('Log file is already active: %s' %
                               self.logfname)
        
        self.log_active = True

        # The three parameters can override constructor defaults
        if logfname: self.logfname = logfname
        if loghead: self.loghead = loghead
        if logmode: self.logmode = logmode
        self.timestamp = timestamp
        self.log_output = log_output
        
        # init depending on the log mode requested
        isfile = os.path.isfile
        logmode = self.logmode

        if logmode == 'append':
            self.logfile = open(self.logfname,'a')

        elif logmode == 'backup':
            if isfile(self.logfname):
                backup_logname = self.logfname+'~'
                # Manually remove any old backup, since os.rename may fail
                # under Windows.
                if isfile(backup_logname):
                    os.remove(backup_logname)
                os.rename(self.logfname,backup_logname)
            self.logfile = open(self.logfname,'w')

        elif logmode == 'global':
            self.logfname = os.path.join(self.shell.home_dir,self.logfname)
            self.logfile = open(self.logfname, 'a')

        elif logmode == 'over':
            if isfile(self.logfname):
                os.remove(self.logfname) 
            self.logfile = open(self.logfname,'w')

        elif logmode == 'rotate':
            if isfile(self.logfname):
                if isfile(self.logfname+'.001~'): 
                    old = glob.glob(self.logfname+'.*~')
                    old.sort()
                    old.reverse()
                    for f in old:
                        root, ext = os.path.splitext(f)
                        num = int(ext[1:-1])+1
                        os.rename(f, root+'.'+`num`.zfill(3)+'~')
                os.rename(self.logfname, self.logfname+'.001~')
            self.logfile = open(self.logfname,'w')
            
        if logmode != 'append':
            self.logfile.write(self.loghead)

        self.logfile.flush()

    def switch_log(self,val):
        """Switch logging on/off. val should be ONLY a boolean."""

        if val not in [False,True,0,1]:
            raise ValueError, \
                  'Call switch_log ONLY with a boolean argument, not with:',val
        
        label = {0:'OFF',1:'ON',False:'OFF',True:'ON'}

        if self.logfile is None:
            print """
Logging hasn't been started yet (use logstart for that).

%logon/%logoff are for temporarily starting and stopping logging for a logfile
which already exists. But you must first start the logging process with
%logstart (optionally giving a logfile name)."""
            
        else:
            if self.log_active == val:
                print 'Logging is already',label[val]
            else:
                print 'Switching logging',label[val]
                self.log_active = not self.log_active
                self.log_active_out = self.log_active

    def logstate(self):
        """Print a status message about the logger."""
        if self.logfile is None:
            print 'Logging has not been activated.'
        else:
            state = self.log_active and 'active' or 'temporarily suspended'
            print 'Filename       :',self.logfname
            print 'Mode           :',self.logmode
            print 'Output logging :',self.log_output
            print 'Timestamping   :',self.timestamp
            print 'State          :',state

    def log(self, line,continuation=None):
        """Write the line to a log and create input cache variables _i*."""

        # update the auto _i tables
        #print '***logging line',line # dbg
        #print '***cache_count', self.shell.outputcache.prompt_count # dbg
        try:
            input_hist = self.shell.user_ns['_ih']
        except:
            print 'userns:',self.shell.user_ns.keys()
            return
        
        if not continuation and line:
            self._iii = self._ii
            self._ii = self._i
            self._i = self._i00
            # put back the final \n of every input line
            self._i00 = line+'\n'
            #print 'Logging input:<%s>' % line  # dbg
            input_hist.append(self._i00)
        #print '---[%s]' % (len(input_hist)-1,) # dbg

        # hackish access to top-level namespace to create _i1,_i2... dynamically
        to_main = {'_i':self._i,'_ii':self._ii,'_iii':self._iii}
        if self.shell.outputcache.do_full_cache:
            in_num = self.shell.outputcache.prompt_count
            # add blank lines if the input cache fell out of sync. This can
            # happen for embedded instances which get killed via C-D and then
            # get resumed.
            while in_num >= len(input_hist):
                input_hist.append('\n')
            # but if the opposite is true (a macro can produce multiple inputs
            # with no output display called), then bring the output counter in
            # sync:
            last_num = len(input_hist)-1
            if in_num != last_num:
                in_num = self.shell.outputcache.prompt_count = last_num
            new_i = '_i%s' % in_num
            if continuation:
                self._i00 = '%s%s\n' % (self.shell.user_ns[new_i],line)
                input_hist[in_num] = self._i00
            to_main[new_i] = self._i00
        self.shell.user_ns.update(to_main)
        self.log_write(line)

    def log_write(self,data,kind='input'):
        """Write data to the log file, if active"""

        if self.log_active and data:
            write = self.logfile.write
            if kind=='input':
                if self.timestamp:
                    write(time.strftime('# %a, %d %b %Y %H:%M:%S\n',
                                        time.localtime()))
                write('%s\n' % data)
            elif kind=='output' and self.log_output:
                odata = '\n'.join(['#[Out]# %s' % s
                                   for s in data.split('\n')])
                write('%s\n' % odata)
            self.logfile.flush()

    def close_log(self):
        self.logfile.close()
        self.logfile = None
        self.logfname = ''
