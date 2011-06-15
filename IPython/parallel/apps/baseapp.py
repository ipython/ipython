#!/usr/bin/env python
# encoding: utf-8
"""
The Base Application class for IPython.parallel apps

Authors:

* Brian Granger
* Min RK

"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from __future__ import with_statement

import os
import logging
import re
import sys

from subprocess import Popen, PIPE

from IPython.core import release
from IPython.core.crashhandler import CrashHandler
from IPython.core.application import (
    BaseIPythonApplication,
    base_aliases as base_ip_aliases,
    base_flags as base_ip_flags
)
from IPython.utils.path import expand_path

from IPython.utils.traitlets import Unicode, Bool, Instance, Dict, List

#-----------------------------------------------------------------------------
# Module errors
#-----------------------------------------------------------------------------

class PIDFileError(Exception):
    pass


#-----------------------------------------------------------------------------
# Crash handler for this application
#-----------------------------------------------------------------------------


_message_template = """\
Oops, $self.app_name crashed. We do our best to make it stable, but...

A crash report was automatically generated with the following information:
  - A verbatim copy of the crash traceback.
  - Data on your current $self.app_name configuration.

It was left in the file named:
\t'$self.crash_report_fname'
If you can email this file to the developers, the information in it will help
them in understanding and correcting the problem.

You can mail it to: $self.contact_name at $self.contact_email
with the subject '$self.app_name Crash Report'.

If you want to do it now, the following command will work (under Unix):
mail -s '$self.app_name Crash Report' $self.contact_email < $self.crash_report_fname

To ensure accurate tracking of this issue, please file a report about it at:
$self.bug_tracker
"""

class ParallelCrashHandler(CrashHandler):
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""

    message_template = _message_template

    def __init__(self, app):
        contact_name = release.authors['Min'][0]
        contact_email = release.authors['Min'][1]
        bug_tracker = 'http://github.com/ipython/ipython/issues'
        super(ParallelCrashHandler,self).__init__(
            app, contact_name, contact_email, bug_tracker
        )


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------
base_aliases = {}
base_aliases.update(base_ip_aliases)
base_aliases.update({
    'profile_dir' : 'ProfileDir.location',
    'log_level' : 'BaseParallelApplication.log_level',
    'work_dir' : 'BaseParallelApplication.work_dir',
    'log_to_file' : 'BaseParallelApplication.log_to_file',
    'clean_logs' : 'BaseParallelApplication.clean_logs',
    'log_url' : 'BaseParallelApplication.log_url',
})

base_flags = {
    'log-to-file' : (
        {'BaseParallelApplication' : {'log_to_file' : True}},
        "send log output to a file"
    )
}
base_flags.update(base_ip_flags)

class BaseParallelApplication(BaseIPythonApplication):
    """The base Application for IPython.parallel apps
    
    Principle extensions to BaseIPyythonApplication:
    
    * work_dir
    * remote logging via pyzmq
    * IOLoop instance
    """

    crash_handler_class = ParallelCrashHandler
    
    def _log_level_default(self):
        # temporarily override default_log_level to INFO
        return logging.INFO

    work_dir = Unicode(os.getcwdu(), config=True,
        help='Set the working dir for the process.'
    )
    def _work_dir_changed(self, name, old, new):
        self.work_dir = unicode(expand_path(new))

    log_to_file = Bool(config=True,
        help="whether to log to a file")

    clean_logs = Bool(False, config=True,
        help="whether to cleanup old logfiles before starting")

    log_url = Unicode('', config=True,
        help="The ZMQ URL of the iplogger to aggregate logging.")

    def _config_files_default(self):
        return ['ipcontroller_config.py', 'ipengine_config.py', 'ipcluster_config.py']
    
    loop = Instance('zmq.eventloop.ioloop.IOLoop')
    def _loop_default(self):
        from zmq.eventloop.ioloop import IOLoop
        return IOLoop.instance()

    aliases = Dict(base_aliases)
    flags = Dict(base_flags)
    
    def initialize(self, argv=None):
        """initialize the app"""
        super(BaseParallelApplication, self).initialize(argv)
        self.to_work_dir()
        self.reinit_logging()
        
    def to_work_dir(self):
        wd = self.work_dir
        if unicode(wd) != os.getcwdu():
            os.chdir(wd)
            self.log.info("Changing to working dir: %s" % wd)
        # This is the working dir by now.
        sys.path.insert(0, '')

    def reinit_logging(self):
        # Remove old log files
        log_dir = self.profile_dir.log_dir
        if self.clean_logs:
            for f in os.listdir(log_dir):
                if re.match(r'%s-\d+\.(log|err|out)'%self.name,f):
                    os.remove(os.path.join(log_dir, f))
        if self.log_to_file:
            # Start logging to the new log file
            log_filename = self.name + u'-' + str(os.getpid()) + u'.log'
            logfile = os.path.join(log_dir, log_filename)
            open_log_file = open(logfile, 'w')
        else:
            open_log_file = None
        if open_log_file is not None:
            self.log.removeHandler(self._log_handler)
            self._log_handler = logging.StreamHandler(open_log_file)
            self._log_formatter = logging.Formatter("[%(name)s] %(message)s")
            self._log_handler.setFormatter(self._log_formatter)
            self.log.addHandler(self._log_handler)

    def write_pid_file(self, overwrite=False):
        """Create a .pid file in the pid_dir with my pid.

        This must be called after pre_construct, which sets `self.pid_dir`.
        This raises :exc:`PIDFileError` if the pid file exists already.
        """
        pid_file = os.path.join(self.profile_dir.pid_dir, self.name + u'.pid')
        if os.path.isfile(pid_file):
            pid = self.get_pid_from_file()
            if not overwrite:
                raise PIDFileError(
                    'The pid file [%s] already exists. \nThis could mean that this '
                    'server is already running with [pid=%s].' % (pid_file, pid)
                )
        with open(pid_file, 'w') as f:
            self.log.info("Creating pid file: %s" % pid_file)
            f.write(repr(os.getpid())+'\n')

    def remove_pid_file(self):
        """Remove the pid file.

        This should be called at shutdown by registering a callback with
        :func:`reactor.addSystemEventTrigger`. This needs to return
        ``None``.
        """
        pid_file = os.path.join(self.profile_dir.pid_dir, self.name + u'.pid')
        if os.path.isfile(pid_file):
            try:
                self.log.info("Removing pid file: %s" % pid_file)
                os.remove(pid_file)
            except:
                self.log.warn("Error removing the pid file: %s" % pid_file)

    def get_pid_from_file(self):
        """Get the pid from the pid file.

        If the  pid file doesn't exist a :exc:`PIDFileError` is raised.
        """
        pid_file = os.path.join(self.profile_dir.pid_dir, self.name + u'.pid')
        if os.path.isfile(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
                return pid
        else:
            raise PIDFileError('pid file not found: %s' % pid_file)
    
    def check_pid(self, pid):
        if os.name == 'nt':
            try:
                import ctypes
                # returns 0 if no such process (of ours) exists
                # positive int otherwise
                p = ctypes.windll.kernel32.OpenProcess(1,0,pid)
            except Exception:
                self.log.warn(
                    "Could not determine whether pid %i is running via `OpenProcess`. "
                    " Making the likely assumption that it is."%pid
                )
                return True
            return bool(p)
        else:
            try:
                p = Popen(['ps','x'], stdout=PIPE, stderr=PIPE)
                output,_ = p.communicate()
            except OSError:
                self.log.warn(
                    "Could not determine whether pid %i is running via `ps x`. "
                    " Making the likely assumption that it is."%pid
                )
                return True
            pids = map(int, re.findall(r'^\W*\d+', output, re.MULTILINE))
            return pid in pids
