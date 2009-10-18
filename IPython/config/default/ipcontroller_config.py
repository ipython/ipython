from IPython.config.loader import Config

c = get_config()

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

c.Global.log_to_file = False
c.Global.import_statements = []
c.Global.reuse_furls = False

# You shouldn't have to edit these
c.Global.log_dir_name = 'log'
c.Global.security_dir_name = 'security'


#-----------------------------------------------------------------------------
# Configure the client services
#-----------------------------------------------------------------------------

c.FCClientServiceFactory.ip = ''
c.FCClientServiceFactory.port = 0 
c.FCClientServiceFactory.location = ''
c.FCClientServiceFactory.secure =  True
c.FCClientServiceFactory.reuse_furls = False
c.FCClientServiceFactory.cert_file = 'ipcontroller-client.pem'

c.FCClientServiceFactory.Interfaces.Task.interface_chain = [
    'IPython.kernel.task.ITaskController',
    'IPython.kernel.taskfc.IFCTaskController'
]
# This is just the filename of the furl file.  The path is always the
# security dir of the cluster directory.
c.FCClientServiceFactory.Interfaces.Task.furl_file = 'ipcontroller-tc.furl'

c.FCClientServiceFactory.Interfaces.MultiEngine.interface_chain = [
    'IPython.kernel.multiengine.IMultiEngine',
    'IPython.kernel.multienginefc.IFCSynchronousMultiEngine'
]
# This is just the filename of the furl file.  The path is always the
# security dir of the cluster directory.
c.FCClientServiceFactory.Interfaces.MultiEngine.furl_file = 'ipcontroller-mec.furl'


#-----------------------------------------------------------------------------
# Configure the engine services
#-----------------------------------------------------------------------------

c.FCEngineServiceFactory.ip = ''
c.FCEngineServiceFactory.port = 0
c.FCEngineServiceFactory.location = ''
c.FCEngineServiceFactory.secure = True
c.FCEngineServiceFactory.reuse_furls = False
c.FCEngineServiceFactory.cert_file = 'ipcontroller-engine.pem'

c.FCEngineServiceFactory.Intefaces.Default.interface_chain = [
    'IPython.kernel.enginefc.IFCControllerBase'
]

# This is just the filename of the furl file.  The path is always the
# security dir of the cluster directory.
c.FCEngineServiceFactory.Intefaces.Default.furl_file = 'ipcontroller-engine.furl'




