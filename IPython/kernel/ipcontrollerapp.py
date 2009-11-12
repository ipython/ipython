#!/usr/bin/env python
# encoding: utf-8
"""
The IPython controller application.
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

import copy
import os
import sys

from twisted.application import service
from twisted.internet import reactor
from twisted.python import log

from IPython.config.loader import Config, NoConfigDefault

from IPython.kernel.clusterdir import (
    ApplicationWithClusterDir, 
    AppWithClusterDirArgParseConfigLoader
)

from IPython.core import release

from IPython.utils.traitlets import Str, Instance

from IPython.kernel import controllerservice

from IPython.kernel.fcutil import FCServiceFactory

#-----------------------------------------------------------------------------
# Default interfaces
#-----------------------------------------------------------------------------


# The default client interfaces for FCClientServiceFactory.interfaces
default_client_interfaces = Config()
default_client_interfaces.Task.interface_chain = [
    'IPython.kernel.task.ITaskController',
    'IPython.kernel.taskfc.IFCTaskController'
]

default_client_interfaces.Task.furl_file = 'ipcontroller-tc.furl'

default_client_interfaces.MultiEngine.interface_chain = [
    'IPython.kernel.multiengine.IMultiEngine',
    'IPython.kernel.multienginefc.IFCSynchronousMultiEngine'
]

default_client_interfaces.MultiEngine.furl_file = u'ipcontroller-mec.furl'

# Make this a dict we can pass to Config.__init__ for the default
default_client_interfaces = dict(copy.deepcopy(default_client_interfaces.items()))



# The default engine interfaces for FCEngineServiceFactory.interfaces
default_engine_interfaces = Config()
default_engine_interfaces.Default.interface_chain = [
    'IPython.kernel.enginefc.IFCControllerBase'
]

default_engine_interfaces.Default.furl_file = u'ipcontroller-engine.furl'

# Make this a dict we can pass to Config.__init__ for the default
default_engine_interfaces = dict(copy.deepcopy(default_engine_interfaces.items()))


#-----------------------------------------------------------------------------
# Service factories
#-----------------------------------------------------------------------------


class FCClientServiceFactory(FCServiceFactory):
    """A Foolscap implementation of the client services."""

    cert_file = Unicode(u'ipcontroller-client.pem', config=True)
    interfaces = Instance(klass=Config, kw=default_client_interfaces,
                          allow_none=False, config=True)


class FCEngineServiceFactory(FCServiceFactory):
    """A Foolscap implementation of the engine services."""

    cert_file = Unicode(u'ipcontroller-engine.pem', config=True)
    interfaces = Instance(klass=dict, kw=default_engine_interfaces,
                          allow_none=False, config=True)


#-----------------------------------------------------------------------------
# The main application
#-----------------------------------------------------------------------------


cl_args = (
    # Client config
    (('--client-ip',), dict(
        type=str, dest='FCClientServiceFactory.ip', default=NoConfigDefault,
        help='The IP address or hostname the controller will listen on for '
        'client connections.',
        metavar='FCClientServiceFactory.ip')
    ),
    (('--client-port',), dict(
        type=int, dest='FCClientServiceFactory.port', default=NoConfigDefault,
        help='The port the controller will listen on for client connections. '
        'The default is to use 0, which will autoselect an open port.',
        metavar='FCClientServiceFactory.port')
    ),
    (('--client-location',), dict(
        type=str, dest='FCClientServiceFactory.location', default=NoConfigDefault,
        help='The hostname or IP that clients should connect to. This does '
        'not control which interface the controller listens on. Instead, this '
        'determines the hostname/IP that is listed in the FURL, which is how '
        'clients know where to connect. Useful if the controller is listening '
        'on multiple interfaces.',
        metavar='FCClientServiceFactory.location')
    ),
    # Engine config
    (('--engine-ip',), dict(
        type=str, dest='FCEngineServiceFactory.ip', default=NoConfigDefault,
        help='The IP address or hostname the controller will listen on for '
        'engine connections.',
        metavar='FCEngineServiceFactory.ip')
    ),
    (('--engine-port',), dict(
        type=int, dest='FCEngineServiceFactory.port', default=NoConfigDefault,
        help='The port the controller will listen on for engine connections. '
        'The default is to use 0, which will autoselect an open port.',
        metavar='FCEngineServiceFactory.port')
    ),
    (('--engine-location',), dict(
        type=str, dest='FCEngineServiceFactory.location', default=NoConfigDefault,
        help='The hostname or IP that engines should connect to. This does '
        'not control which interface the controller listens on. Instead, this '
        'determines the hostname/IP that is listed in the FURL, which is how '
        'engines know where to connect. Useful if the controller is listening '
        'on multiple interfaces.',
        metavar='FCEngineServiceFactory.location')
    ),
    # Global config
    (('--log-to-file',), dict(
        action='store_true', dest='Global.log_to_file', default=NoConfigDefault,
        help='Log to a file in the log directory (default is stdout)')
    ),
    (('-r','--reuse-furls'), dict(
        action='store_true', dest='Global.reuse_furls', default=NoConfigDefault,
        help='Try to reuse all FURL files. If this is not set all FURL files '
        'are deleted before the controller starts. This must be set if '
        'specific ports are specified by --engine-port or --client-port.')
    ),
    (('--no-secure',), dict(
        action='store_false', dest='Global.secure', default=NoConfigDefault,
        help='Turn off SSL encryption for all connections.')
    ),
    (('--secure',), dict(
        action='store_true', dest='Global.secure', default=NoConfigDefault,
        help='Turn off SSL encryption for all connections.')
    )
)


class IPControllerAppCLConfigLoader(AppWithClusterDirArgParseConfigLoader):

    arguments = cl_args


default_config_file_name = u'ipcontroller_config.py'


class IPControllerApp(ApplicationWithClusterDir):

    name = u'ipcontroller'
    description = 'Start the IPython controller for parallel computing.'
    config_file_name = default_config_file_name
    auto_create_cluster_dir = True

    def create_default_config(self):
        super(IPControllerApp, self).create_default_config()
        self.default_config.Global.reuse_furls = False
        self.default_config.Global.secure = True
        self.default_config.Global.import_statements = []
        self.default_config.Global.clean_logs = True

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPControllerAppCLConfigLoader(
            description=self.description, 
            version=release.version
        )

    def post_load_command_line_config(self):
        # Now setup reuse_furls
        c = self.command_line_config
        if hasattr(c.Global, 'reuse_furls'):
            c.FCClientServiceFactory.reuse_furls = c.Global.reuse_furls
            c.FCEngineServiceFactory.reuse_furls = c.Global.reuse_furls
            del c.Global.reuse_furls
        if hasattr(c.Global, 'secure'):
            c.FCClientServiceFactory.secure = c.Global.secure
            c.FCEngineServiceFactory.secure = c.Global.secure
            del c.Global.secure

    def construct(self):
        # I am a little hesitant to put these into InteractiveShell itself.
        # But that might be the place for them
        sys.path.insert(0, '')

        self.start_logging()
        self.import_statements()

        # Create the service hierarchy
        self.main_service = service.MultiService()
        # The controller service
        controller_service = controllerservice.ControllerService()
        controller_service.setServiceParent(self.main_service)
        # The client tub and all its refereceables
        csfactory = FCClientServiceFactory(self.master_config, controller_service)
        client_service = csfactory.create()
        client_service.setServiceParent(self.main_service)
        # The engine tub
        esfactory = FCEngineServiceFactory(self.master_config, controller_service)
        engine_service = esfactory.create()
        engine_service.setServiceParent(self.main_service)

    def import_statements(self):
        statements = self.master_config.Global.import_statements
        for s in statements:
            try:
                log.msg("Executing statement: '%s'" % s)
                exec s in globals(), locals()
            except:
                log.msg("Error running statement: %s" % s)

    def start_app(self):
        # Start the controller service.
        self.main_service.startService()
        # Write the .pid file overwriting old ones. This allow multiple
        # controllers to clober each other. But Windows is not cleaning
        # these up properly.
        self.write_pid_file(overwrite=True)
        # cd to the cluster_dir as our working directory.
        os.chdir(self.master_config.Global.cluster_dir)
        # Add a trigger to delete the .pid file upon shutting down.
        reactor.addSystemEventTrigger('during','shutdown', self.remove_pid_file)
        reactor.run()


def launch_new_instance():
    """Create and run the IPython controller"""
    app = IPControllerApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()

