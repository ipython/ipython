from IPython.config.loader import Config

c = get_config()

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

# Basic Global config attributes

# Start up messages are logged to stdout using the logging module.
# These all happen before the twisted reactor is started and are
# useful for debugging purposes. Can be (10=DEBUG,20=INFO,30=WARN,40=CRITICAL) 
# and smaller is more verbose.
# c.Global.log_level = 20

# Log to a file in cluster_dir/log, otherwise just log to sys.stdout.
# c.Global.log_to_file = False

# Remove old logs from cluster_dir/log before starting.
# c.Global.clean_logs = True

# A list of Python statements that will be run before starting the 
# controller. This is provided because occasionally certain things need to 
# be imported in the controller for pickling to work.
# c.Global.import_statements = ['import math']

# Reuse the controller's FURL files. If False, FURL files are regenerated
# each time the controller is run. If True, they will be reused, *but*, you
# also must set the network ports by hand. If set, this will override the
# values set for the client and engine connections below.
# c.Global.reuse_furls = True

# Enable SSL encryption on all connections to the controller. If set, this
# will override the values set for the client and engine connections below.
# c.Global.secure = True

# The working directory for the process. The application will use os.chdir
# to change to this directory before starting.
# c.Global.working_dir = os.getcwd()

#-----------------------------------------------------------------------------
# Configure the client services
#-----------------------------------------------------------------------------

# Basic client service config attributes

# The network interface the controller will listen on for client connections.
# This should be an IP address or hostname of the controller's host. The empty
# string means listen on all interfaces.
# c.FCClientServiceFactory.ip = ''

# The TCP/IP port the controller will listen on for client connections. If 0
# a random port will be used. If the controller's host has a firewall running
# it must allow incoming traffic on this port.
# c.FCClientServiceFactory.port = 0

# The client learns how to connect to the controller by looking at the
# location field embedded in the FURL. If this field is empty, all network
# interfaces that the controller is listening on will be listed. To have the
# client connect on a particular interface, list it here.
# c.FCClientServiceFactory.location = ''

# Use SSL encryption for the client connection.
# c.FCClientServiceFactory.secure =  True

# Reuse the client FURL each time the controller is started. If set, you must
# also pick a specific network port above (FCClientServiceFactory.port).
# c.FCClientServiceFactory.reuse_furls = False

#-----------------------------------------------------------------------------
# Configure the engine services
#-----------------------------------------------------------------------------

# Basic config attributes for the engine services.

# The network interface the controller will listen on for engine connections.
# This should be an IP address or hostname of the controller's host. The empty
# string means listen on all interfaces.
# c.FCEngineServiceFactory.ip = ''

# The TCP/IP port the controller will listen on for engine connections. If 0
# a random port will be used. If the controller's host has a firewall running
# it must allow incoming traffic on this port.
# c.FCEngineServiceFactory.port = 0

# The engine learns how to connect to the controller by looking at the
# location field embedded in the FURL. If this field is empty, all network
# interfaces that the controller is listening on will be listed. To have the
# client connect on a particular interface, list it here.
# c.FCEngineServiceFactory.location = ''

# Use SSL encryption for the engine connection.
# c.FCEngineServiceFactory.secure = True

# Reuse the client FURL each time the controller is started. If set, you must
# also pick a specific network port above (FCClientServiceFactory.port).
# c.FCEngineServiceFactory.reuse_furls = False

#-----------------------------------------------------------------------------
# Developer level configuration attributes
#-----------------------------------------------------------------------------

# You shouldn't have to modify anything in this section. These attributes
# are more for developers who want to change the behavior of the controller
# at a fundamental level.

# c.FCClientServiceFactory.cert_file = u'ipcontroller-client.pem'

# default_client_interfaces = Config()
# default_client_interfaces.Task.interface_chain = [
#     'IPython.kernel.task.ITaskController',
#     'IPython.kernel.taskfc.IFCTaskController'
# ]
# 
# default_client_interfaces.Task.furl_file = u'ipcontroller-tc.furl'
# 
# default_client_interfaces.MultiEngine.interface_chain = [
#     'IPython.kernel.multiengine.IMultiEngine',
#     'IPython.kernel.multienginefc.IFCSynchronousMultiEngine'
# ]
# 
# default_client_interfaces.MultiEngine.furl_file = u'ipcontroller-mec.furl'
# 
# c.FCEngineServiceFactory.interfaces = default_client_interfaces

# c.FCEngineServiceFactory.cert_file = u'ipcontroller-engine.pem'

# default_engine_interfaces = Config()
# default_engine_interfaces.Default.interface_chain = [
#     'IPython.kernel.enginefc.IFCControllerBase'
# ]
# 
# default_engine_interfaces.Default.furl_file = u'ipcontroller-engine.furl'
# 
# c.FCEngineServiceFactory.interfaces = default_engine_interfaces
