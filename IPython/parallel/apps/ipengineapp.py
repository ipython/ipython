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

import json
import os
import sys

import zmq
from zmq.eventloop import ioloop

from IPython.parallel.apps.clusterdir import (
    ClusterDirApplication,
    ClusterDir,
    base_aliases,
    # ClusterDirConfigLoader
)
from IPython.zmq.log import EnginePUBHandler

from IPython.config.configurable import Configurable
from IPython.parallel.streamsession import StreamSession
from IPython.parallel.engine.engine import EngineFactory
from IPython.parallel.engine.streamkernel import Kernel
from IPython.parallel.util import disambiguate_url

from IPython.utils.importstring import import_item
from IPython.utils.traitlets import Str, Bool, Unicode, Dict, List, CStr


#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------

#: The default config file name for this application
default_config_file_name = u'ipengine_config.py'

_description = """Start an IPython engine for parallel computing.\n\n

IPython engines run in parallel and perform computations on behalf of a client
and controller. A controller needs to be started before the engines. The
engine can be configured using command line options or using a cluster
directory. Cluster directories contain config, log and security files and are
usually located in your ipython directory and named as "cluster_<profile>".
See the `profile` and `cluster_dir` options for details.
"""


#-----------------------------------------------------------------------------
# MPI configuration
#-----------------------------------------------------------------------------

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

class MPI(Configurable):
    """Configurable for MPI initialization"""
    use = Str('', config=True,
        help='How to enable MPI (mpi4py, pytrilinos, or empty string to disable).'
        )

    def _on_use_changed(self, old, new):
        # load default init script if it's not set
        if not self.init_script:
            self.init_script = self.default_inits.get(new, '')

    init_script = Str('', config=True,
        help="Initialization code for MPI")

    default_inits = Dict({'mpi4py' : mpi4py_init, 'pytrilinos':pytrilinos_init},
        config=True)


#-----------------------------------------------------------------------------
# Main application
#-----------------------------------------------------------------------------


class IPEngineApp(ClusterDirApplication):

    app_name = Unicode(u'ipengine')
    description = Unicode(_description)
    default_config_file_name = default_config_file_name
    classes = List([ClusterDir, StreamSession, EngineFactory, Kernel, MPI])

    startup_script = Unicode(u'', config=True,
        help='specify a script to be run at startup')
    startup_command = Str('', config=True,
            help='specify a command to be run at startup')

    url_file = Unicode(u'', config=True,
        help="""The full location of the file containing the connection information for
        the controller. If this is not given, the file must be in the
        security directory of the cluster directory.  This location is
        resolved using the `profile` or `cluster_dir` options.""",
        )

    url_file_name = Unicode(u'ipcontroller-engine.json')

    aliases = Dict(dict(
        config = 'IPEngineApp.config_file',
        file = 'IPEngineApp.url_file',
        c = 'IPEngineApp.startup_command',
        s = 'IPEngineApp.startup_script',

        ident = 'StreamSession.session',
        user = 'StreamSession.username',
        exec_key = 'StreamSession.keyfile',

        url = 'EngineFactory.url',
        ip = 'EngineFactory.ip',
        transport = 'EngineFactory.transport',
        port = 'EngineFactory.regport',
        location = 'EngineFactory.location',

        timeout = 'EngineFactory.timeout',

        profile = "ClusterDir.profile",
        cluster_dir = 'ClusterDir.location',

        mpi = 'MPI.use',

        log_level = 'IPEngineApp.log_level',
    ))

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
        config = self.config
        # Find the actual controller key file
        if not self.url_file:
            self.url_file = os.path.join(
                self.cluster_dir.security_dir,
                self.url_file_name
            )
        
    def init_engine(self):
        # This is the working dir by now.
        sys.path.insert(0, '')
        config = self.config
        # print config
        self.find_url_file()

        # if os.path.exists(config.Global.key_file) and config.Global.secure:
        #     config.SessionFactory.exec_key = config.Global.key_file
        if os.path.exists(self.url_file):
            with open(self.url_file) as f:
                d = json.loads(f.read())
                for k,v in d.iteritems():
                    if isinstance(v, unicode):
                        d[k] = v.encode()
            if d['exec_key']:
                config.StreamSession.key = d['exec_key']
            d['url'] = disambiguate_url(d['url'], d['location'])
            config.EngineFactory.url = d['url']
            config.EngineFactory.location = d['location']
        
        try:
            exec_lines = config.Kernel.exec_lines
        except AttributeError:
            config.Kernel.exec_lines = []
            exec_lines = config.Kernel.exec_lines
        
        if self.startup_script:
            enc = sys.getfilesystemencoding() or 'utf8'
            cmd="execfile(%r)"%self.startup_script.encode(enc)
            exec_lines.append(cmd)
        if self.startup_command:
            exec_lines.append(self.startup_command)

        # Create the underlying shell class and Engine
        # shell_class = import_item(self.master_config.Global.shell_class)
        # print self.config
        try:
            self.engine = EngineFactory(config=config, log=self.log)
        except:
            self.log.error("Couldn't start the Engine", exc_info=True)
            self.exit(1)
        
        # self.start_logging()

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

    # def start_logging(self):
    #     super(IPEngineApp, self).start_logging()
    #     if self.master_config.Global.log_url:
    #         context = self.engine.context
    #         lsock = context.socket(zmq.PUB)
    #         lsock.connect(self.master_config.Global.log_url)
    #         handler = EnginePUBHandler(self.engine, lsock)
    #         handler.setLevel(self.log_level)
    #         self.log.addHandler(handler)
    #
    def init_mpi(self):
        global mpi
        self.mpi = MPI(config=self.config)

        mpi_import_statement = self.mpi.init_script
        if mpi_import_statement:
            try:
                self.log.info("Initializing MPI:")
                self.log.info(mpi_import_statement)
                exec mpi_import_statement in globals()
            except:
                mpi = None
        else:
            mpi = None


    def start(self):
        self.engine.start()
        try:
            self.engine.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Engine Interrupted, shutting down...\n")


def launch_new_instance():
    """Create and run the IPython engine"""
    app = IPEngineApp()
    app.parse_command_line()
    cl_config = app.config
    app.init_clusterdir()
    # app.load_config_file()
    # print app.config
    if app.config_file:
        app.load_config_file(app.config_file)
    else:
        app.load_config_file(app.default_config_file_name, path=app.cluster_dir.location)

    # command-line should *override* config file, but command-line is necessary
    # to determine clusterdir, etc.
    app.update_config(cl_config)

    # print app.config
    app.to_work_dir()
    app.init_mpi()
    app.init_engine()
    print app.config
    app.start()


if __name__ == '__main__':
    launch_new_instance()

