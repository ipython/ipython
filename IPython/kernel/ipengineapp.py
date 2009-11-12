#!/usr/bin/env python
# encoding: utf-8
"""
The IPython controller application
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
import sys

from twisted.application import service
from twisted.internet import reactor
from twisted.python import log

from IPython.config.loader import NoConfigDefault

from IPython.kernel.clusterdir import (
    ApplicationWithClusterDir, 
    AppWithClusterDirArgParseConfigLoader
)
from IPython.core import release

from IPython.utils.importstring import import_item

from IPython.kernel.engineservice import EngineService
from IPython.kernel.fcutil import Tub
from IPython.kernel.engineconnector import EngineConnector

#-----------------------------------------------------------------------------
# The main application
#-----------------------------------------------------------------------------


cl_args = (
    # Controller config
    (('--furl-file',), dict(
        type=unicode, dest='Global.furl_file', default=NoConfigDefault,
        help='The full location of the file containing the FURL of the '
        'controller. If this is not given, the FURL file must be in the '
        'security directory of the cluster directory.  This location is '
        'resolved using the --profile and --app-dir options.',
        metavar='Global.furl_file')
    ),
    # MPI
    (('--mpi',), dict(
        type=str, dest='MPI.use', default=NoConfigDefault,
        help='How to enable MPI (mpi4py, pytrilinos, or empty string to disable).',
        metavar='MPI.use')
    ),
    # Global config
    (('--log-to-file',), dict(
        action='store_true', dest='Global.log_to_file', default=NoConfigDefault,
        help='Log to a file in the log directory (default is stdout)')
    )
)


class IPEngineAppCLConfigLoader(AppWithClusterDirArgParseConfigLoader):

    arguments = cl_args


mpi4py_init = """from mpi4py import MPI as mpi
mpi.size = mpi.COMM_WORLD.Get_size()
mpi.rank = mpi.COMM_WORLD.Get_rank()
"""

pytrilinos_init = """from PyTrilinos import Epetra
class SimpleStruct:
pass
mpi = SimpleStruct()
mpi.rank = 0
mpi.size = 0
"""


default_config_file_name = u'ipengine_config.py'


class IPEngineApp(ApplicationWithClusterDir):

    name = u'ipengine'
    description = 'Start the IPython engine for parallel computing.'
    config_file_name = default_config_file_name
    auto_create_cluster_dir = True

    def create_default_config(self):
        super(IPEngineApp, self).create_default_config()

        # The engine should not clean logs as we don't want to remove the
        # active log files of other running engines.
        self.default_config.Global.clean_logs = False

        # Global config attributes
        self.default_config.Global.exec_lines = []
        self.default_config.Global.shell_class = 'IPython.kernel.core.interpreter.Interpreter'

        # Configuration related to the controller
        # This must match the filename (path not included) that the controller
        # used for the FURL file.
        self.default_config.Global.furl_file_name = u'ipcontroller-engine.furl'
        # If given, this is the actual location of the controller's FURL file.
        # If not, this is computed using the profile, app_dir and furl_file_name
        self.default_config.Global.furl_file = u''

        # The max number of connection attemps and the initial delay between
        # those attemps.
        self.default_config.Global.connect_delay = 0.1
        self.default_config.Global.connect_max_tries = 15

        # MPI related config attributes
        self.default_config.MPI.use = ''
        self.default_config.MPI.mpi4py = mpi4py_init
        self.default_config.MPI.pytrilinos = pytrilinos_init

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPEngineAppCLConfigLoader(
            description=self.description, 
            version=release.version
        )

    def post_load_command_line_config(self):
        pass

    def pre_construct(self):
        super(IPEngineApp, self).pre_construct()
        self.find_cont_furl_file()

    def find_cont_furl_file(self):
        """Set the furl file.

        Here we don't try to actually see if it exists for is valid as that
        is hadled by the connection logic.
        """
        config = self.master_config
        # Find the actual controller FURL file
        if not config.Global.furl_file:
            try_this = os.path.join(
                config.Global.cluster_dir, 
                config.Global.security_dir,
                config.Global.furl_file_name
            )
            config.Global.furl_file = try_this

    def construct(self):
        # This is the working dir by now.
        sys.path.insert(0, '')

        self.start_mpi()
        self.start_logging()

        # Create the underlying shell class and EngineService
        shell_class = import_item(self.master_config.Global.shell_class)
        self.engine_service = EngineService(shell_class, mpi=mpi)

        self.exec_lines()

        # Create the service hierarchy
        self.main_service = service.MultiService()
        self.engine_service.setServiceParent(self.main_service)
        self.tub_service = Tub()
        self.tub_service.setServiceParent(self.main_service)
        # This needs to be called before the connection is initiated
        self.main_service.startService()

        # This initiates the connection to the controller and calls
        # register_engine to tell the controller we are ready to do work
        self.engine_connector = EngineConnector(self.tub_service)

        log.msg("Using furl file: %s" % self.master_config.Global.furl_file)

        reactor.callWhenRunning(self.call_connect)

    def call_connect(self):
        d = self.engine_connector.connect_to_controller(
            self.engine_service, 
            self.master_config.Global.furl_file,
            self.master_config.Global.connect_delay,
            self.master_config.Global.connect_max_tries
        )

        def handle_error(f):
            log.msg('Error connecting to controller. This usually means that '
            'i) the controller was not started, ii) a firewall was blocking '
            'the engine from connecting to the controller or iii) the engine '
            ' was not pointed at the right FURL file:')
            log.msg(f.getErrorMessage())
            reactor.callLater(0.1, reactor.stop)

        d.addErrback(handle_error)

    def start_mpi(self):
        global mpi
        mpikey = self.master_config.MPI.use
        mpi_import_statement = self.master_config.MPI.get(mpikey, None)
        if mpi_import_statement is not None:
            try:
                self.log.info("Initializing MPI:")
                self.log.info(mpi_import_statement)
                exec mpi_import_statement in globals()
            except:
                mpi = None
        else:
            mpi = None

    def exec_lines(self):
        for line in self.master_config.Global.exec_lines:
            try:
                log.msg("Executing statement: '%s'" % line)
                self.engine_service.execute(line)
            except:
                log.msg("Error executing statement: %s" % line)

    def start_app(self):
        reactor.run()


def launch_new_instance():
    """Create and run the IPython controller"""
    app = IPEngineApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

