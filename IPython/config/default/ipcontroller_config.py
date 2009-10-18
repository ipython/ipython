from IPython.config.loader import Config

c = get_config()

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

# Basic Global config attributes
# c.Global.log_to_file = False
# c.Global.import_statements = ['import math']
# c.Global.reuse_furls = True
# c.Global.secure = True

# You shouldn't have to modify these
# c.Global.log_dir_name = 'log'
# c.Global.security_dir_name = 'security'


#-----------------------------------------------------------------------------
# Configure the client services
#-----------------------------------------------------------------------------

# Basic client service config attributes
# c.FCClientServiceFactory.ip = ''
# c.FCClientServiceFactory.port = 0
# c.FCClientServiceFactory.location = ''
# c.FCClientServiceFactory.secure =  True
# c.FCClientServiceFactory.reuse_furls = False

# You shouldn't have to modify the rest of this section
# c.FCClientServiceFactory.cert_file = 'ipcontroller-client.pem'

# default_client_interfaces = Config()
# default_client_interfaces.Task.interface_chain = [
#     'IPython.kernel.task.ITaskController',
#     'IPython.kernel.taskfc.IFCTaskController'
# ]
# 
# default_client_interfaces.Task.furl_file = 'ipcontroller-tc.furl'
# 
# default_client_interfaces.MultiEngine.interface_chain = [
#     'IPython.kernel.multiengine.IMultiEngine',
#     'IPython.kernel.multienginefc.IFCSynchronousMultiEngine'
# ]
# 
# default_client_interfaces.MultiEngine.furl_file = 'ipcontroller-mec.furl'
# 
# c.FCEngineServiceFactory.interfaces = default_client_interfaces

#-----------------------------------------------------------------------------
# Configure the engine services
#-----------------------------------------------------------------------------

# Basic config attributes for the engine services
# c.FCEngineServiceFactory.ip = ''
# c.FCEngineServiceFactory.port = 0
# c.FCEngineServiceFactory.location = ''
# c.FCEngineServiceFactory.secure = True
# c.FCEngineServiceFactory.reuse_furls = False

# You shouldn't have to modify the rest of this section
# c.FCEngineServiceFactory.cert_file = 'ipcontroller-engine.pem'

# default_engine_interfaces = Config()
# default_engine_interfaces.Default.interface_chain = [
#     'IPython.kernel.enginefc.IFCControllerBase'
# ]
# 
# default_engine_interfaces.Default.furl_file = 'ipcontroller-engine.furl'
# 
# c.FCEngineServiceFactory.interfaces = default_engine_interfaces
