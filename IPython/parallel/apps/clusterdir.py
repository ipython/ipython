#!/usr/bin/env python
# encoding: utf-8
"""
The IPython cluster directory
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

from __future__ import with_statement

import os
import logging
import re
import shutil
import sys

from subprocess import Popen, PIPE

from IPython.config.loader import PyFileConfigLoader, Config
from IPython.config.configurable import Configurable
from IPython.config.application import Application
from IPython.core.crashhandler import CrashHandler
from IPython.core.newapplication import BaseIPythonApplication
from IPython.core import release
from IPython.utils.path import (
    get_ipython_package_dir,
    get_ipython_dir,
    expand_path
)
from IPython.utils.traitlets import Unicode, Bool, Instance, Dict

#-----------------------------------------------------------------------------
# Module errors
#-----------------------------------------------------------------------------

class ClusterDirError(Exception):
    pass


class PIDFileError(Exception):
    pass


#-----------------------------------------------------------------------------
# Class for managing cluster directories
#-----------------------------------------------------------------------------

class ClusterDir(Configurable):
    """An object to manage the cluster directory and its resources.

    The cluster directory is used by :command:`ipengine`, 
    :command:`ipcontroller` and :command:`ipclsuter` to manage the
    configuration, logging and security of these applications.

    This object knows how to find, create and manage these directories. This
    should be used by any code that want's to handle cluster directories.
    """

    security_dir_name = Unicode('security')
    log_dir_name = Unicode('log')
    pid_dir_name = Unicode('pid')
    security_dir = Unicode(u'')
    log_dir = Unicode(u'')
    pid_dir = Unicode(u'')

    auto_create = Bool(False,
        help="""Whether to automatically create the ClusterDirectory if it does
        not exist""")
    overwrite = Bool(False,
        help="""Whether to overwrite existing config files""")
    location = Unicode(u'', config=True,
        help="""Set the cluster dir. This overrides the logic used by the
        `profile` option.""",
        )
    profile = Unicode(u'default', config=True,
        help="""The string name of the profile to be used. This determines the name
        of the cluster dir as: cluster_<profile>. The default profile is named
        'default'.  The cluster directory is resolve this way if the
        `cluster_dir` option is not used."""
        )

    _location_isset = Bool(False) # flag for detecting multiply set location
    _new_dir = Bool(False) # flag for whether a new dir was created

    def __init__(self, **kwargs):
        # make sure auto_create,overwrite are set *before* location
        for name in ('auto_create', 'overwrite'):
            v = kwargs.pop(name, None)
            if v is not None:
                setattr(self, name, v)
        super(ClusterDir, self).__init__(**kwargs)
        if not self.location:
            self._profile_changed('profile', 'default', self.profile)

    def _location_changed(self, name, old, new):
        if self._location_isset:
            raise RuntimeError("Cannot set ClusterDir more than once.")
        self._location_isset = True
        if not os.path.isdir(new):
            if self.auto_create:# or self.config.ClusterDir.auto_create:
                os.makedirs(new)
                self._new_dir = True
            else:
                raise ClusterDirError('Directory not found: %s' % new)
        
        # ensure config files exist:
        self.copy_all_config_files(overwrite=self.overwrite)
        self.security_dir = os.path.join(new, self.security_dir_name)
        self.log_dir = os.path.join(new, self.log_dir_name)
        self.pid_dir = os.path.join(new, self.pid_dir_name)
        self.check_dirs()

    def _profile_changed(self, name, old, new):
        if self._location_isset:
            raise RuntimeError("ClusterDir already set.  Cannot set by profile.")
        self.location = os.path.join(get_ipython_dir(), 'cluster_'+new)

    def _log_dir_changed(self, name, old, new):
        self.check_log_dir()

    def check_log_dir(self):
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

    def _security_dir_changed(self, name, old, new):
        self.check_security_dir()

    def check_security_dir(self):
        if not os.path.isdir(self.security_dir):
            os.mkdir(self.security_dir, 0700)
        os.chmod(self.security_dir, 0700)

    def _pid_dir_changed(self, name, old, new):
        self.check_pid_dir()

    def check_pid_dir(self):
        if not os.path.isdir(self.pid_dir):
            os.mkdir(self.pid_dir, 0700)
        os.chmod(self.pid_dir, 0700)

    def check_dirs(self):
        self.check_security_dir()
        self.check_log_dir()
        self.check_pid_dir()

    def copy_config_file(self, config_file, path=None, overwrite=False):
        """Copy a default config file into the active cluster directory.

        Default configuration files are kept in :mod:`IPython.config.default`.
        This function moves these from that location to the working cluster
        directory.
        """
        if path is None:
            import IPython.config.default
            path = IPython.config.default.__file__.split(os.path.sep)[:-1]
            path = os.path.sep.join(path)
        src = os.path.join(path, config_file)
        dst = os.path.join(self.location, config_file)
        if not os.path.isfile(dst) or overwrite:
            shutil.copy(src, dst)

    def copy_all_config_files(self, path=None, overwrite=False):
        """Copy all config files into the active cluster directory."""
        for f in [u'ipcontroller_config.py', u'ipengine_config.py',
                  u'ipcluster_config.py']:
            self.copy_config_file(f, path=path, overwrite=overwrite)

    @classmethod
    def create_cluster_dir(csl, cluster_dir):
        """Create a new cluster directory given a full path.

        Parameters
        ----------
        cluster_dir : str
            The full path to the cluster directory.  If it does exist, it will
            be used.  If not, it will be created.
        """
        return ClusterDir(location=cluster_dir)

    @classmethod
    def create_cluster_dir_by_profile(cls, path, profile=u'default'):
        """Create a cluster dir by profile name and path.

        Parameters
        ----------
        path : str
            The path (directory) to put the cluster directory in.
        profile : str
            The name of the profile.  The name of the cluster directory will
            be "cluster_<profile>".
        """
        if not os.path.isdir(path):
            raise ClusterDirError('Directory not found: %s' % path)
        cluster_dir = os.path.join(path, u'cluster_' + profile)
        return ClusterDir(location=cluster_dir)

    @classmethod
    def find_cluster_dir_by_profile(cls, ipython_dir, profile=u'default'):
        """Find an existing cluster dir by profile name, return its ClusterDir.

        This searches through a sequence of paths for a cluster dir.  If it
        is not found, a :class:`ClusterDirError` exception will be raised.

        The search path algorithm is:
        1. ``os.getcwd()``
        2. ``ipython_dir``
        3. The directories found in the ":" separated 
           :env:`IPCLUSTER_DIR_PATH` environment variable.

        Parameters
        ----------
        ipython_dir : unicode or str
            The IPython directory to use.
        profile : unicode or str
            The name of the profile.  The name of the cluster directory
            will be "cluster_<profile>".
        """
        dirname = u'cluster_' + profile
        cluster_dir_paths = os.environ.get('IPCLUSTER_DIR_PATH','')
        if cluster_dir_paths:
            cluster_dir_paths = cluster_dir_paths.split(':')
        else:
            cluster_dir_paths = []
        paths = [os.getcwd(), ipython_dir] + cluster_dir_paths
        for p in paths:
            cluster_dir = os.path.join(p, dirname)
            if os.path.isdir(cluster_dir):
                return ClusterDir(location=cluster_dir)
        else:
            raise ClusterDirError('Cluster directory not found in paths: %s' % dirname)

    @classmethod
    def find_cluster_dir(cls, cluster_dir):
        """Find/create a cluster dir and return its ClusterDir.

        This will create the cluster directory if it doesn't exist.

        Parameters
        ----------
        cluster_dir : unicode or str
            The path of the cluster directory.  This is expanded using
            :func:`IPython.utils.genutils.expand_path`.
        """
        cluster_dir = expand_path(cluster_dir)
        if not os.path.isdir(cluster_dir):
            raise ClusterDirError('Cluster directory not found: %s' % cluster_dir)
        return ClusterDir(location=cluster_dir)


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

class ClusterDirCrashHandler(CrashHandler):
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""

    message_template = _message_template

    def __init__(self, app):
        contact_name = release.authors['Min'][0]
        contact_email = release.authors['Min'][1]
        bug_tracker = 'http://github.com/ipython/ipython/issues'
        super(ClusterDirCrashHandler,self).__init__(
            app, contact_name, contact_email, bug_tracker
        )


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------
base_aliases = {
    'profile' : "ClusterDir.profile",
    'cluster_dir' : 'ClusterDir.location',
    'auto_create' : 'ClusterDirApplication.auto_create',
    'log_level' : 'ClusterApplication.log_level',
    'work_dir' : 'ClusterApplication.work_dir',
    'log_to_file' : 'ClusterApplication.log_to_file',
    'clean_logs' : 'ClusterApplication.clean_logs',
    'log_url' : 'ClusterApplication.log_url',
}

base_flags = {
    'debug' : ( {"ClusterApplication" : {"log_level" : logging.DEBUG}}, "set loglevel to DEBUG"),
    'quiet' : ( {"ClusterApplication" : {"log_level" : logging.CRITICAL}}, "set loglevel to CRITICAL (minimal output)"),
    'log-to-file' : ( {"ClusterApplication" : {"log_to_file" : True}}, "redirect log output to a file"),
}
for k,v in base_flags.iteritems():
    base_flags[k] = (Config(v[0]),v[1])

class ClusterApplication(BaseIPythonApplication):
    """An application that puts everything into a cluster directory.

    Instead of looking for things in the ipython_dir, this type of application
    will use its own private directory called the "cluster directory"
    for things like config files, log files, etc.

    The cluster directory is resolved as follows:

    * If the ``--cluster-dir`` option is given, it is used.
    * If ``--cluster-dir`` is not given, the application directory is 
      resolve using the profile name as ``cluster_<profile>``. The search 
      path for this directory is then i) cwd if it is found there
      and ii) in ipython_dir otherwise.

    The config file for the application is to be put in the cluster
    dir and named the value of the ``config_file_name`` class attribute.
    """

    crash_handler_class = ClusterDirCrashHandler
    auto_create_cluster_dir = Bool(True, config=True,
        help="whether to create the cluster_dir if it doesn't exist")
    cluster_dir = Instance(ClusterDir)
    classes = [ClusterDir]
    
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

    clean_logs = Bool(False, shortname='--clean-logs', config=True,
        help="whether to cleanup old logfiles before starting")

    log_url = Unicode('', shortname='--log-url', config=True,
        help="The ZMQ URL of the iplogger to aggregate logging.")

    config_file = Unicode(u'', config=True,
        help="""Path to ipcontroller configuration file.  The default is to use
         <appname>_config.py, as found by cluster-dir."""
    )
    
    loop = Instance('zmq.eventloop.ioloop.IOLoop')
    def _loop_default(self):
        from zmq.eventloop.ioloop import IOLoop
        return IOLoop.instance()

    aliases = Dict(base_aliases)
    flags = Dict(base_flags)

    def init_clusterdir(self):
        """This resolves the cluster directory.

        This tries to find the cluster directory and if successful, it will
        have done:
        * Sets ``self.cluster_dir_obj`` to the :class:`ClusterDir` object for 
          the application.
        * Sets ``self.cluster_dir`` attribute of the application and config
          objects.

        The algorithm used for this is as follows:
        1. Try ``Global.cluster_dir``.
        2. Try using ``Global.profile``.
        3. If both of these fail and ``self.auto_create_cluster_dir`` is
           ``True``, then create the new cluster dir in the IPython directory.
        4. If all fails, then raise :class:`ClusterDirError`.
        """
        try:
            self.cluster_dir = ClusterDir(auto_create=self.auto_create_cluster_dir, config=self.config)
        except ClusterDirError as e:
            self.log.fatal("Error initializing cluster dir: %s"%e)
            self.log.fatal("A cluster dir must be created before running this command.")
            self.log.fatal("Do 'ipcluster create -h' or 'ipcluster list -h' for more "
            "information about creating and listing cluster dirs."
            )
            self.exit(1)
            
        if self.cluster_dir._new_dir:
            self.log.info('Creating new cluster dir: %s' % \
                            self.cluster_dir.location)
        else:
            self.log.info('Using existing cluster dir: %s' % \
                            self.cluster_dir.location)
    
    def initialize(self, argv=None):
        """initialize the app"""
        self.init_crash_handler()
        self.parse_command_line(argv)
        cl_config = self.config
        self.init_clusterdir()
        if self.config_file:
            self.load_config_file(self.config_file)
        elif self.default_config_file_name:
            try:
                self.load_config_file(self.default_config_file_name, 
                                        path=self.cluster_dir.location)
            except IOError:
                self.log.warn("Warning: Default config file not found")
        # command-line should *override* config file, but command-line is necessary
        # to determine clusterdir, etc.
        self.update_config(cl_config)
        self.to_work_dir()
        self.reinit_logging()
        
    def to_work_dir(self):
        wd = self.work_dir
        if unicode(wd) != os.getcwdu():
            os.chdir(wd)
            self.log.info("Changing to working dir: %s" % wd)
        # This is the working dir by now.
        sys.path.insert(0, '')

    def load_config_file(self, filename, path=None):
        """Load a .py based config file by filename and path."""
        # use config.application.Application.load_config
        # instead of inflexible core.newapplication.BaseIPythonApplication.load_config
        return Application.load_config_file(self, filename, path=path)
    #
    # def load_default_config_file(self):
    #     """Load a .py based config file by filename and path."""
    #     return BaseIPythonApplication.load_config_file(self)

    # disable URL-logging
    def reinit_logging(self):
        # Remove old log files
        log_dir = self.cluster_dir.log_dir
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
        pid_file = os.path.join(self.cluster_dir.pid_dir, self.name + u'.pid')
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
        pid_file = os.path.join(self.cluster_dir.pid_dir, self.name + u'.pid')
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
        pid_file = os.path.join(self.cluster_dir.pid_dir, self.name + u'.pid')
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
