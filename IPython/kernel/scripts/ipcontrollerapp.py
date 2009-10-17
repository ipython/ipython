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
import os
import sys

from twisted.application import service
from twisted.internet import reactor, defer
from twisted.python import log

from IPython.config.loader import Config, NoConfigDefault

from IPython.core.application import Application, IPythonArgParseConfigLoader
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
# Components for creating services
#-----------------------------------------------------------------------------


# The default client interfaces for FCClientServiceFactory.Interfaces
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



# The default engine interfaces for FCEngineServiceFactory.Interfaces
default_engine_interfaces = Config()
default_engine_interfaces.Default.interface_chain = [
    'IPython.kernel.enginefc.IFCControllerBase'
]
default_engine_interfaces.Default.furl_file = 'ipcontroller-engine.furl'

# Make this a dict we can pass to Config.__init__ for the default
default_engine_interfaces = dict(copy.deepcopy(default_engine_interfaces.items()))



class FCClientServiceFactory(FCServiceFactory):
    """A Foolscap implementation of the client services."""

    cert_file = Str('ipcontroller-client.pem', config=True)
    Interfaces = Instance(klass=Config, kw=default_client_interfaces,
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
    (('-x',), dict(
        action='store_false', dest='FCClientServiceFactory.secure', default=NoConfigDefault,
        help='Turn off all client security.')
    ),
    (('--client-cert-file',), dict(
        type=str, dest='FCClientServiceFactory.cert_file', default=NoConfigDefault,
        help='File to store the client SSL certificate in.',
        metavar='FCClientServiceFactory.cert_file')
    ),
    (('--task-furl-file',), dict(
        type=str, dest='FCClientServiceFactory.Interfaces.Task.furl_file', default=NoConfigDefault,
        help='File to store the FURL in for task clients to connect with.',
        metavar='FCClientServiceFactory.Interfaces.Task.furl_file')
    ),
    (('--multiengine-furl-file',), dict(
        type=str, dest='FCClientServiceFactory.Interfaces.MultiEngine.furl_file', default=NoConfigDefault,
        help='File to store the FURL in for multiengine clients to connect with.',
        metavar='FCClientServiceFactory.Interfaces.MultiEngine.furl_file')
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
    (('-y',), dict(
        action='store_false', dest='FCEngineServiceFactory.secure', default=NoConfigDefault,
        help='Turn off all engine security.')
    ),
    (('--engine-cert-file',), dict(
        type=str, dest='FCEngineServiceFactory.cert_file', default=NoConfigDefault,
        help='File to store the client SSL certificate in.',
        metavar='FCEngineServiceFactory.cert_file')
    ),
    (('--engine-furl-file',), dict(
        type=str, dest='FCEngineServiceFactory.Interfaces.Default.furl_file', default=NoConfigDefault,
        help='File to store the FURL in for engines to connect with.',
        metavar='FCEngineServiceFactory.Interfaces.Default.furl_file')
    ),
    # Global config
    (('-l','--logfile'), dict(
        type=str, dest='Global.logfile', default=NoConfigDefault,
        help='Log file name (default is stdout)',
        metavar='Global.logfile')
    ),
    (('-r',), dict(
        action='store_true', dest='Global.reuse_furls', default=NoConfigDefault,
        help='Try to reuse all FURL files.')
    )
)


class IPControllerAppCLConfigLoader(IPythonArgParseConfigLoader):

    arguments = cl_args


_default_config_file_name = 'ipcontroller_config.py'

class IPControllerApp(Application):

    name = 'ipcontroller'
    config_file_name = _default_config_file_name

    def create_default_config(self):
        super(IPControllerApp, self).create_default_config()
        self.default_config.Global.logfile = ''
        self.default_config.Global.reuse_furls = False
        self.default_config.Global.import_statements = []

    def create_command_line_config(self):
        """Create and return a command line config loader."""

        return IPControllerAppCLConfigLoader(
            description="Start an IPython controller",
            version=release.version)

    def construct(self):
        # I am a little hesitant to put these into InteractiveShell itself.
        # But that might be the place for them
        sys.path.insert(0, '')

        self.start_logging()
        self.import_statements()
        self.reuse_furls()

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
        logfile = self.master_config.Global.logfile
        if logfile:
            logfile = logfile + str(os.getpid()) + '.log'
            try:
                openLogFile = open(logfile, 'w')
            except:
                openLogFile = sys.stdout
        else:
            openLogFile = sys.stdout
        log.startLogging(openLogFile)

    def import_statements(self):
        statements = self.master_config.Global.import_statements
        for s in statements:
            try:
                exec s in globals(), locals()
            except:
                log.msg("Error running import statement: %s" % s)

    def reuse_furls(self):
        # This logic might need to be moved into the components
        # Delete old furl files unless the reuse_furls is set
        reuse = self.master_config.Global.reuse_furls
        # if not reuse:
        #     paths = (
        #         self.master_config.FCEngineServiceFactory.Interfaces.Default.furl_file,
        #         self.master_config.FCClientServiceFactory.Interfaces.Task.furl_file,
        #         self.master_config.FCClientServiceFactory.Interfaces.MultiEngine.furl_file
        #     )
        #     for p in paths:
        #         if os.path.isfile(p):
        #             os.remove(p)

    def start_app(self):
        # Start the controller service and set things running
        self.main_service.startService()
        reactor.run()

if __name__ == '__main__':
    app = IPControllerApp()
    app.start()
