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

import copy
import logging
import os
import sys

from twisted.application import service
from twisted.internet import reactor, defer
from twisted.python import log

from IPython.config.loader import Config, NoConfigDefault

from IPython.core.application import (
    ApplicationWithDir, 
    AppWithDirArgParseConfigLoader
)

from IPython.core import release

from IPython.utils.traitlets import Int, Str, Bool, Instance
from IPython.utils.importstring import import_item

from IPython.kernel import controllerservice
from IPython.kernel.configobjfactory import (
    ConfiguredObjectFactory,
    AdaptedConfiguredObjectFactory
)

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

default_client_interfaces.MultiEngine.furl_file = 'ipcontroller-mec.furl'

# Make this a dict we can pass to Config.__init__ for the default
default_client_interfaces = dict(copy.deepcopy(default_client_interfaces.items()))



# The default engine interfaces for FCEngineServiceFactory.interfaces
default_engine_interfaces = Config()
default_engine_interfaces.Default.interface_chain = [
    'IPython.kernel.enginefc.IFCControllerBase'
]

default_engine_interfaces.Default.furl_file = 'ipcontroller-engine.furl'

# Make this a dict we can pass to Config.__init__ for the default
default_engine_interfaces = dict(copy.deepcopy(default_engine_interfaces.items()))


#-----------------------------------------------------------------------------
# Service factories
#-----------------------------------------------------------------------------


class FCClientServiceFactory(FCServiceFactory):
    """A Foolscap implementation of the client services."""

    cert_file = Str('ipcontroller-client.pem', config=True)
    interfaces = Instance(klass=Config, kw=default_client_interfaces,
                          allow_none=False, config=True)


class FCEngineServiceFactory(FCServiceFactory):
    """A Foolscap implementation of the engine services."""

    cert_file = Str('ipcontroller-engine.pem', config=True)
    interfaces = Instance(klass=dict, kw=default_engine_interfaces,
                          allow_none=False, config=True)


#-----------------------------------------------------------------------------
# The main application
#-----------------------------------------------------------------------------


cl_args = (
    # Client config
    (('--client-ip',), dict(
        type=str, dest='FCClientServiceFactory.ip', default=NoConfigDefault,
        help='The IP address or hostname the controller will listen on for client connections.',
        metavar='FCClientServiceFactory.ip')
    ),
    (('--client-port',), dict(
        type=int, dest='FCClientServiceFactory.port', default=NoConfigDefault,
        help='The port the controller will listen on for client connections.',
        metavar='FCClientServiceFactory.port')
    ),
    (('--client-location',), dict(
        type=str, dest='FCClientServiceFactory.location', default=NoConfigDefault,
        help='The hostname or ip that clients should connect to.',
        metavar='FCClientServiceFactory.location')
    ),
    # Engine config
    (('--engine-ip',), dict(
        type=str, dest='FCEngineServiceFactory.ip', default=NoConfigDefault,
        help='The IP address or hostname the controller will listen on for engine connections.',
        metavar='FCEngineServiceFactory.ip')
    ),
    (('--engine-port',), dict(
        type=int, dest='FCEngineServiceFactory.port', default=NoConfigDefault,
        help='The port the controller will listen on for engine connections.',
        metavar='FCEngineServiceFactory.port')
    ),
    (('--engine-location',), dict(
        type=str, dest='FCEngineServiceFactory.location', default=NoConfigDefault,
        help='The hostname or ip that engines should connect to.',
        metavar='FCEngineServiceFactory.location')
    ),
    # Global config
    (('--log-to-file',), dict(
        action='store_true', dest='Global.log_to_file', default=NoConfigDefault,
        help='Log to a file in the log directory (default is stdout)')
    ),
    (('-r','--reuse-furls'), dict(
        action='store_true', dest='Global.reuse_furls', default=NoConfigDefault,
        help='Try to reuse all FURL files.')
    ),
    (('-ns','--no-security'), dict(
        action='store_false', dest='Global.secure', default=NoConfigDefault,
        help='Turn off SSL encryption for all connections.')
    )
)


class IPControllerAppCLConfigLoader(AppWithDirArgParseConfigLoader):

    arguments = cl_args


default_config_file_name = 'ipcontroller_config.py'


class IPControllerApp(ApplicationWithDir):

    name = 'ipcontroller'
    app_dir_basename = 'cluster'
    description = 'Start the IPython controller for parallel computing.'
    config_file_name = default_config_file_name

    def create_default_config(self):
        super(IPControllerApp, self).create_default_config()
        self.default_config.Global.reuse_furls = False
        self.default_config.Global.secure = True
        self.default_config.Global.import_statements = []
        self.default_config.Global.log_dir_name = 'log'
        self.default_config.Global.security_dir_name = 'security'
        self.default_config.Global.log_to_file = False

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPControllerAppCLConfigLoader(
            description=self.description, 
            version=release.version
        )

    def post_load_command_line_config(self):
        # Now setup reuse_furls
        if hasattr(self.command_line_config.Global, 'reuse_furls'):
            self.command_line_config.FCClientServiceFactory.reuse_furls = \
                self.command_line_config.Global.reuse_furls
            self.command_line_config.FCEngineServiceFactory.reuse_furls = \
                self.command_line_config.Global.reuse_furls
            del self.command_line_config.Global.reuse_furls
        if hasattr(self.command_line_config.Global, 'secure'):
            self.command_line_config.FCClientServiceFactory.secure = \
                self.command_line_config.Global.secure
            self.command_line_config.FCEngineServiceFactory.secure = \
                self.command_line_config.Global.secure
            del self.command_line_config.Global.secure

    def pre_construct(self):
        config = self.master_config
        # Now set the security_dir and log_dir and create them.  We use
        # the names an construct the absolute paths.
        security_dir = os.path.join(config.Global.app_dir,
                                    config.Global.security_dir_name)
        log_dir = os.path.join(config.Global.app_dir, 
                               config.Global.log_dir_name)
        if not os.path.isdir(security_dir):
            os.mkdir(security_dir, 0700)
        else:
            os.chmod(security_dir, 0700)
        if not os.path.isdir(log_dir):
            os.mkdir(log_dir, 0777)

        self.security_dir = config.Global.security_dir = security_dir
        self.log_dir = config.Global.log_dir = log_dir
        self.log.info("Log directory set to: %s" % self.log_dir)
        self.log.info("Security directory set to: %s" % self.security_dir)

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

    def start_logging(self):
        if self.master_config.Global.log_to_file:
            log_filename = self.name + '-' + str(os.getpid()) + '.log'
            logfile = os.path.join(self.log_dir, log_filename)
            open_log_file = open(logfile, 'w')
        else:
            open_log_file = sys.stdout
        log.startLogging(open_log_file)

    def import_statements(self):
        statements = self.master_config.Global.import_statements
        for s in statements:
            try:
                log.msg("Executing statement: '%s'" % s)
                exec s in globals(), locals()
            except:
                log.msg("Error running statement: %s" % s)

    def start_app(self):
        # Start the controller service and set things running
        self.main_service.startService()
        reactor.run()


def launch_new_instance():
    """Create and run the IPython controller"""
    app = IPControllerApp()
    app.start()
