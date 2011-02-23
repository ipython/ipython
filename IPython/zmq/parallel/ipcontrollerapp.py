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
import logging
import socket
import stat
import sys
import uuid

import zmq
from zmq.log.handlers import PUBHandler
from zmq.utils import jsonapi as json

from IPython.config.loader import Config
from IPython.zmq.parallel import factory
from IPython.zmq.parallel.controller import ControllerFactory
from IPython.zmq.parallel.clusterdir import (
    ApplicationWithClusterDir,
    ClusterDirConfigLoader
)
# from IPython.kernel.fcutil import FCServiceFactory, FURLError
from IPython.utils.traitlets import Instance, Unicode

from util import disambiguate_ip_address, split_url


#-----------------------------------------------------------------------------
# Module level variables
#-----------------------------------------------------------------------------


#: The default config file name for this application
default_config_file_name = u'ipcontrollerz_config.py'


_description = """Start the IPython controller for parallel computing.

The IPython controller provides a gateway between the IPython engines and
clients. The controller needs to be started before the engines and can be
configured using command line options or using a cluster directory. Cluster
directories contain config, log and security files and are usually located in
your ipython directory and named as "cluster_<profile>". See the --profile
and --cluster-dir options for details.
"""

#-----------------------------------------------------------------------------
# Default interfaces
#-----------------------------------------------------------------------------

# The default client interfaces for FCClientServiceFactory.interfaces
default_client_interfaces = Config()
default_client_interfaces.Default.url_file = 'ipcontroller-client.url'

# Make this a dict we can pass to Config.__init__ for the default
default_client_interfaces = dict(copy.deepcopy(default_client_interfaces.items()))



# The default engine interfaces for FCEngineServiceFactory.interfaces
default_engine_interfaces = Config()
default_engine_interfaces.Default.url_file = u'ipcontroller-engine.url'

# Make this a dict we can pass to Config.__init__ for the default
default_engine_interfaces = dict(copy.deepcopy(default_engine_interfaces.items()))


#-----------------------------------------------------------------------------
# Service factories
#-----------------------------------------------------------------------------

# 
# class FCClientServiceFactory(FCServiceFactory):
#     """A Foolscap implementation of the client services."""
# 
#     cert_file = Unicode(u'ipcontroller-client.pem', config=True)
#     interfaces = Instance(klass=Config, kw=default_client_interfaces,
#                           allow_none=False, config=True)
# 
# 
# class FCEngineServiceFactory(FCServiceFactory):
#     """A Foolscap implementation of the engine services."""
# 
#     cert_file = Unicode(u'ipcontroller-engine.pem', config=True)
#     interfaces = Instance(klass=dict, kw=default_engine_interfaces,
#                           allow_none=False, config=True)
# 

#-----------------------------------------------------------------------------
# Command line options
#-----------------------------------------------------------------------------


class IPControllerAppConfigLoader(ClusterDirConfigLoader):

    def _add_arguments(self):
        super(IPControllerAppConfigLoader, self)._add_arguments()
        paa = self.parser.add_argument
        
        ## Hub Config:
        paa('--mongodb', 
            dest='HubFactory.db_class', action='store_const',
            const='IPython.zmq.parallel.mongodb.MongoDB', 
            help='Use MongoDB task storage [default: in-memory]')
        paa('--hb',
            type=int, dest='HubFactory.hb', nargs=2,
            help='The (2) ports the Hub\'s Heartmonitor will use for the heartbeat '
            'connections [default: random]',
            metavar='Hub.hb_ports')
        paa('--ping',
            type=int, dest='HubFactory.ping',
            help='The frequency at which the Hub pings the engines for heartbeats '
            ' (in ms) [default: 100]',
            metavar='Hub.ping')
        
        # Client config
        paa('--client-ip',
            type=str, dest='HubFactory.client_ip', 
            help='The IP address or hostname the Hub will listen on for '
            'client connections. Both engine-ip and client-ip can be set simultaneously '
            'via --ip [default: loopback]',
            metavar='Hub.client_ip')
        paa('--client-transport',
            type=str, dest='HubFactory.client_transport', 
            help='The ZeroMQ transport the Hub will use for '
            'client connections. Both engine-transport and client-transport can be set simultaneously '
            'via --transport [default: tcp]',
            metavar='Hub.client_transport')
        paa('--query',
            type=int, dest='HubFactory.query_port', 
            help='The port on which the Hub XREP socket will listen for result queries from clients [default: random]',
            metavar='Hub.query_port')
        paa('--notifier',
            type=int, dest='HubFactory.notifier_port', 
            help='The port on which the Hub PUB socket will listen for notification connections [default: random]',
            metavar='Hub.notifier_port')
        
        # Engine config
        paa('--engine-ip',
            type=str, dest='HubFactory.engine_ip', 
            help='The IP address or hostname the Hub will listen on for '
            'engine connections. This applies to the Hub and its schedulers'
            'engine-ip and client-ip can be set simultaneously '
            'via --ip [default: loopback]',
            metavar='Hub.engine_ip')
        paa('--engine-transport',
            type=str, dest='HubFactory.engine_transport', 
            help='The ZeroMQ transport the Hub will use for '
            'client connections. Both engine-transport and client-transport can be set simultaneously '
            'via --transport [default: tcp]',
            metavar='Hub.engine_transport')
        
        # Scheduler config
        paa('--mux',
            type=int, dest='ControllerFactory.mux', nargs=2,
            help='The (2) ports the MUX scheduler will listen on for client,engine '
            'connections, respectively [default: random]',
            metavar='Scheduler.mux_ports')
        paa('--task',
            type=int, dest='ControllerFactory.task', nargs=2,
            help='The (2) ports the Task scheduler will listen on for client,engine '
            'connections, respectively [default: random]',
            metavar='Scheduler.task_ports')
        paa('--control',
            type=int, dest='ControllerFactory.control', nargs=2,
            help='The (2) ports the Control scheduler will listen on for client,engine '
            'connections, respectively [default: random]',
            metavar='Scheduler.control_ports')
        paa('--iopub',
            type=int, dest='ControllerFactory.iopub', nargs=2,
            help='The (2) ports the IOPub scheduler will listen on for client,engine '
            'connections, respectively [default: random]',
            metavar='Scheduler.iopub_ports')
            
        paa('--scheme',
            type=str, dest='HubFactory.scheme',
            choices = ['pure', 'lru', 'plainrandom', 'weighted', 'twobin','leastload'],
            help='select the task scheduler scheme  [default: Python LRU]',
            metavar='Scheduler.scheme')
        paa('--usethreads',
            dest='ControllerFactory.usethreads', action="store_true",
            help='Use threads instead of processes for the schedulers',
            )
        paa('--hwm',
            dest='ControllerFactory.hwm', type=int,
            help='specify the High Water Mark (HWM) for the downstream '
            'socket in the pure ZMQ scheduler. This is the maximum number '
            'of allowed outstanding tasks on each engine.',
            )
        
        ## Global config
        paa('--log-to-file',
            action='store_true', dest='Global.log_to_file',
            help='Log to a file in the log directory (default is stdout)')
        paa('--log-url',
            type=str, dest='Global.log_url',
            help='Broadcast logs to an iploggerz process [default: disabled]')
        paa('-r','--reuse-files', 
            action='store_true', dest='Global.reuse_files',
            help='Try to reuse existing json connection files.')
        paa('--no-secure',
            action='store_false', dest='Global.secure',
            help='Turn off execution keys (default).')
        paa('--secure',
            action='store_true', dest='Global.secure',
            help='Turn on execution keys.')
        paa('--execkey',
            type=str, dest='Global.exec_key',
            help='path to a file containing an execution key.',
            metavar='keyfile')
        paa('--ssh',
            type=str, dest='Global.sshserver',
            help='ssh url for clients to use when connecting to the Controller '
            'processes. It should be of the form: [user@]server[:port]. The '
            'Controller\'s listening addresses must be accessible from the ssh server',
            metavar='Global.sshserver')
        paa('--location',
            type=str, dest='Global.location',
            help="The external IP or domain name of this machine, used for disambiguating "
            "engine and client connections.",
            metavar='Global.location')
        factory.add_session_arguments(self.parser)
        factory.add_registration_arguments(self.parser)


#-----------------------------------------------------------------------------
# The main application
#-----------------------------------------------------------------------------


class IPControllerApp(ApplicationWithClusterDir):

    name = u'ipcontrollerz'
    description = _description
    command_line_loader = IPControllerAppConfigLoader
    default_config_file_name = default_config_file_name
    auto_create_cluster_dir = True
    

    def create_default_config(self):
        super(IPControllerApp, self).create_default_config()
        # Don't set defaults for Global.secure or Global.reuse_furls
        # as those are set in a component.
        self.default_config.Global.import_statements = []
        self.default_config.Global.clean_logs = True
        self.default_config.Global.secure = True
        self.default_config.Global.reuse_files = False
        self.default_config.Global.exec_key = "exec_key.key"
        self.default_config.Global.sshserver = None
        self.default_config.Global.location = None

    def pre_construct(self):
        super(IPControllerApp, self).pre_construct()
        c = self.master_config
        # The defaults for these are set in FCClientServiceFactory and
        # FCEngineServiceFactory, so we only set them here if the global
        # options have be set to override the class level defaults.
        
        # if hasattr(c.Global, 'reuse_furls'):
        #     c.FCClientServiceFactory.reuse_furls = c.Global.reuse_furls
        #     c.FCEngineServiceFactory.reuse_furls = c.Global.reuse_furls
        #     del c.Global.reuse_furls
        # if hasattr(c.Global, 'secure'):
        #     c.FCClientServiceFactory.secure = c.Global.secure
        #     c.FCEngineServiceFactory.secure = c.Global.secure
        #     del c.Global.secure
    
    def save_connection_dict(self, fname, cdict):
        """save a connection dict to json file."""
        c = self.master_config
        url = cdict['url']
        location = cdict['location']
        if not location:
            try:
                proto,ip,port = split_url(url)
            except AssertionError:
                pass
            else:
                location = socket.gethostbyname_ex(socket.gethostname())[2][-1]
            cdict['location'] = location
        fname = os.path.join(c.Global.security_dir, fname)
        with open(fname, 'w') as f:
            f.write(json.dumps(cdict, indent=2))
        os.chmod(fname, stat.S_IRUSR|stat.S_IWUSR)
    
    def load_config_from_json(self):
        """load config from existing json connector files."""
        c = self.master_config
        # load from engine config
        with open(os.path.join(c.Global.security_dir, 'ipcontroller-engine.json')) as f:
            cfg = json.loads(f.read())
        key = c.SessionFactory.exec_key = cfg['exec_key']
        xport,addr = cfg['url'].split('://')
        c.HubFactory.engine_transport = xport
        ip,ports = addr.split(':')
        c.HubFactory.engine_ip = ip
        c.HubFactory.regport = int(ports)
        c.Global.location = cfg['location']
        
        # load client config
        with open(os.path.join(c.Global.security_dir, 'ipcontroller-client.json')) as f:
            cfg = json.loads(f.read())
        assert key == cfg['exec_key'], "exec_key mismatch between engine and client keys"
        xport,addr = cfg['url'].split('://')
        c.HubFactory.client_transport = xport
        ip,ports = addr.split(':')
        c.HubFactory.client_ip = ip
        c.Global.sshserver = cfg['ssh']
        assert int(ports) == c.HubFactory.regport, "regport mismatch"
    
    def construct(self):
        # This is the working dir by now.
        sys.path.insert(0, '')
        c = self.master_config
        
        self.import_statements()
        reusing = c.Global.reuse_files
        if reusing:
            try:
                self.load_config_from_json()
            except (AssertionError,IOError):
                reusing=False
        # check again, because reusing may have failed:
        if reusing:
            pass
        elif c.Global.secure:
            keyfile = os.path.join(c.Global.security_dir, c.Global.exec_key)
            key = str(uuid.uuid4())
            with open(keyfile, 'w') as f:
                f.write(key)
            os.chmod(keyfile, stat.S_IRUSR|stat.S_IWUSR)
            c.SessionFactory.exec_key = key
        else:
            c.SessionFactory.exec_key = ''
            key = None
        
        try:
            self.factory = ControllerFactory(config=c, logname=self.log.name)
            self.start_logging()
            self.factory.construct()
        except:
            self.log.error("Couldn't construct the Controller", exc_info=True)
            self.exit(1)
        
        if not reusing:
            # save to new json config files
            f = self.factory
            cdict = {'exec_key' : key,
                    'ssh' : c.Global.sshserver,
                    'url' : "%s://%s:%s"%(f.client_transport, f.client_ip, f.regport),
                    'location' : c.Global.location
                    }
            self.save_connection_dict('ipcontroller-client.json', cdict)
            edict = cdict
            edict['url']="%s://%s:%s"%((f.client_transport, f.client_ip, f.regport))
            self.save_connection_dict('ipcontroller-engine.json', edict)
        
    
    def save_urls(self):
        """save the registration urls to files."""
        c = self.master_config
        
        sec_dir = c.Global.security_dir
        cf = self.factory
        
        with open(os.path.join(sec_dir, 'ipcontroller-engine.url'), 'w') as f:
            f.write("%s://%s:%s"%(cf.engine_transport, cf.engine_ip, cf.regport))
        
        with open(os.path.join(sec_dir, 'ipcontroller-client.url'), 'w') as f:
            f.write("%s://%s:%s"%(cf.client_transport, cf.client_ip, cf.regport))
        
    
    def import_statements(self):
        statements = self.master_config.Global.import_statements
        for s in statements:
            try:
                self.log.msg("Executing statement: '%s'" % s)
                exec s in globals(), locals()
            except:
                self.log.msg("Error running statement: %s" % s)

    def start_logging(self):
        super(IPControllerApp, self).start_logging()
        if self.master_config.Global.log_url:
            context = self.factory.context
            lsock = context.socket(zmq.PUB)
            lsock.connect(self.master_config.Global.log_url)
            handler = PUBHandler(lsock)
            handler.root_topic = 'controller'
            handler.setLevel(self.log_level)
            self.log.addHandler(handler)
    # 
    def start_app(self):
        # Start the subprocesses:
        self.factory.start()
        self.write_pid_file(overwrite=True)
        try:
            self.factory.loop.start()
        except KeyboardInterrupt:
            self.log.critical("Interrupted, Exiting...\n")


def launch_new_instance():
    """Create and run the IPython controller"""
    app = IPControllerApp()
    app.start()


if __name__ == '__main__':
    launch_new_instance()
