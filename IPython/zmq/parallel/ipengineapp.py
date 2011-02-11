#!/usr/bin/env python
# encoding: utf-8
"""
The IPython engine application
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
import json

import zmq
from zmq.eventloop import ioloop

from IPython.zmq.parallel.clusterdir import (
    ApplicationWithClusterDir,
    ClusterDirConfigLoader
)
from IPython.zmq.log import EnginePUBHandler

from IPython.zmq.parallel import factory
from IPython.zmq.parallel.engine import EngineFactory
from IPython.zmq.parallel.streamkernel import Kernel
from IPython.utils.importstring import import_item

from util import disambiguate_url

#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------

#: The default config file name for this application
default_config_file_name = u'ipengine_config.py'


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


_description = """Start an IPython engine for parallel computing.\n\n

IPython engines run in parallel and perform computations on behalf of a client
and controller. A controller needs to be started before the engines. The
engine can be configured using command line options or using a cluster
directory. Cluster directories contain config, log and security files and are
usually located in your .ipython directory and named as "cluster_<profile>".
See the --profile and --cluster-dir options for details.
"""

#-----------------------------------------------------------------------------
# Command line options
#-----------------------------------------------------------------------------


class IPEngineAppConfigLoader(ClusterDirConfigLoader):

    def _add_arguments(self):
        super(IPEngineAppConfigLoader, self)._add_arguments()
        paa = self.parser.add_argument
        # Controller config
        paa('--file',
            type=unicode, dest='Global.url_file',
            help='The full location of the file containing the connection information fo '
            'controller. If this is not given, the file must be in the '
            'security directory of the cluster directory.  This location is '
            'resolved using the --profile and --app-dir options.',
            metavar='Global.url_file')
        # MPI
        paa('--mpi',
            type=str, dest='MPI.use',
            help='How to enable MPI (mpi4py, pytrilinos, or empty string to disable).',
            metavar='MPI.use')
        # Global config
        paa('--log-to-file',
            action='store_true', dest='Global.log_to_file',
            help='Log to a file in the log directory (default is stdout)')
        paa('--log-url',
            dest='Global.log_url',
            help="url of ZMQ logger, as started with iploggerz")
        # paa('--execkey',
        #     type=str, dest='Global.exec_key',
        #     help='path to a file containing an execution key.',
        #     metavar='keyfile')
        # paa('--no-secure',
        #     action='store_false', dest='Global.secure',
        #     help='Turn off execution keys.')
        # paa('--secure',
        #     action='store_true', dest='Global.secure',
        #     help='Turn on execution keys (default).')
        # init command
        paa('-c',
            type=str, dest='Global.extra_exec_lines',
            help='specify a command to be run at startup')
        
        factory.add_session_arguments(self.parser)
        factory.add_registration_arguments(self.parser)


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------


class IPEngineApp(ApplicationWithClusterDir):

    name = u'ipenginez'
    description = _description
    command_line_loader = IPEngineAppConfigLoader
    default_config_file_name = default_config_file_name
    auto_create_cluster_dir = True

    def create_default_config(self):
        super(IPEngineApp, self).create_default_config()

        # The engine should not clean logs as we don't want to remove the
        # active log files of other running engines.
        self.default_config.Global.clean_logs = False
        self.default_config.Global.secure = True

        # Global config attributes
        self.default_config.Global.exec_lines = []
        self.default_config.Global.extra_exec_lines = ''

        # Configuration related to the controller
        # This must match the filename (path not included) that the controller
        # used for the FURL file.
        self.default_config.Global.url_file = u''
        self.default_config.Global.url_file_name = u'ipcontroller-engine.json'
        # If given, this is the actual location of the controller's FURL file.
        # If not, this is computed using the profile, app_dir and furl_file_name
        # self.default_config.Global.key_file_name = u'exec_key.key'
        # self.default_config.Global.key_file = u''

        # MPI related config attributes
        self.default_config.MPI.use = ''
        self.default_config.MPI.mpi4py = mpi4py_init
        self.default_config.MPI.pytrilinos = pytrilinos_init

    def post_load_command_line_config(self):
        pass

    def pre_construct(self):
        super(IPEngineApp, self).pre_construct()
        # self.find_cont_url_file()
        self.find_url_file()
        if self.master_config.Global.extra_exec_lines:
            self.master_config.Global.exec_lines.append(self.master_config.Global.extra_exec_lines)

    # def find_key_file(self):
    #     """Set the key file.
    # 
    #     Here we don't try to actually see if it exists for is valid as that
    #     is hadled by the connection logic.
    #     """
    #     config = self.master_config
    #     # Find the actual controller key file
    #     if not config.Global.key_file:
    #         try_this = os.path.join(
    #             config.Global.cluster_dir, 
    #             config.Global.security_dir,
    #             config.Global.key_file_name
    #         )
    #         config.Global.key_file = try_this
        
    def find_url_file(self):
        """Set the key file.

        Here we don't try to actually see if it exists for is valid as that
        is hadled by the connection logic.
        """
        config = self.master_config
        # Find the actual controller key file
        if not config.Global.url_file:
            try_this = os.path.join(
                config.Global.cluster_dir, 
                config.Global.security_dir,
                config.Global.url_file_name
            )
            config.Global.url_file = try_this
        
    def construct(self):
        # This is the working dir by now.
        sys.path.insert(0, '')
        config = self.master_config
        # if os.path.exists(config.Global.key_file) and config.Global.secure:
        #     config.SessionFactory.exec_key = config.Global.key_file
        if os.path.exists(config.Global.url_file):
            with open(config.Global.url_file) as f:
                d = json.loads(f.read())
                for k,v in d.iteritems():
                    if isinstance(v, unicode):
                        d[k] = v.encode()
            if d['exec_key']:
                config.SessionFactory.exec_key = d['exec_key']
            d['url'] = disambiguate_url(d['url'], d['location'])
            config.RegistrationFactory.url=d['url']
            config.EngineFactory.location = d['location']
        
        
        
        config.Kernel.exec_lines = config.Global.exec_lines

        self.start_mpi()

        # Create the underlying shell class and EngineService
        # shell_class = import_item(self.master_config.Global.shell_class)
        try:
            self.engine = EngineFactory(config=config, logname=self.log.name)
        except:
            self.log.error("Couldn't start the Engine", exc_info=True)
            self.exit(1)
        
        self.start_logging()

        # Create the service hierarchy
        # self.main_service = service.MultiService()
        # self.engine_service.setServiceParent(self.main_service)
        # self.tub_service = Tub()
        # self.tub_service.setServiceParent(self.main_service)
        # # This needs to be called before the connection is initiated
        # self.main_service.startService()

        # This initiates the connection to the controller and calls
        # register_engine to tell the controller we are ready to do work
        # self.engine_connector = EngineConnector(self.tub_service)

        # self.log.info("Using furl file: %s" % self.master_config.Global.furl_file)

        # reactor.callWhenRunning(self.call_connect)


    def start_logging(self):
        super(IPEngineApp, self).start_logging()
        if self.master_config.Global.log_url:
            context = self.engine.context
            lsock = context.socket(zmq.PUB)
            lsock.connect(self.master_config.Global.log_url)
            handler = EnginePUBHandler(self.engine, lsock)
            handler.setLevel(self.log_level)
            self.log.addHandler(handler)
    
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


    def start_app(self):
        self.engine.start()
        try:
            self.engine.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Engine Interrupted, shutting down...\n")


def launch_new_instance():
    """Create and run the IPython controller"""
    app = IPEngineApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

