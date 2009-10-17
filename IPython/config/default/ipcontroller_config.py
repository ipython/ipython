from IPython.config.loader import Config

c = get_config()

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

c.Global.logfile = ''
c.Global.import_statement = ''
c.Global.reuse_furls = False


#-----------------------------------------------------------------------------
# Configure the client services
#-----------------------------------------------------------------------------

c.FCClientServiceFactory.ip = ''
c.FCClientServiceFactory.port = 0 
c.FCClientServiceFactory.location = ''
c.FCClientServiceFactory.secure =  True
c.FCClientServiceFactory.cert_file = 'ipcontroller-client.pem'

c.FCClientServiceFactory.Interfaces.Task.interface_chain = [
    'IPython.kernel.task.ITaskController',
    'IPython.kernel.taskfc.IFCTaskController'
]
c.FCClientServiceFactory.Interfaces.Task.furl_file = 'ipcontroller-tc.furl'

c.FCClientServiceFactory.Interfaces.MultiEngine.interface_chain = [
    'IPython.kernel.multiengine.IMultiEngine',
    'IPython.kernel.multienginefc.IFCSynchronousMultiEngine'
]
c.FCClientServiceFactory.Interfaces.MultiEngine.furl_file = 'ipcontroller-mec.furl'


#-----------------------------------------------------------------------------
# Configure the engine services
#-----------------------------------------------------------------------------

c.FCEngineServiceFactory.ip = ''
c.FCEngineServiceFactory.port = 0
c.FCEngineServiceFactory.location = ''
c.FCEngineServiceFactory.secure = True
c.FCEngineServiceFactory.cert_file = 'ipcontroller-engine.pem'

engine_config = Config()
engine_config.furl_file = 
c.Global.engine_furl_file = 'ipcontroller-engine.furl'
c.Global.engine_fc_interface = 'IPython.kernel.enginefc.IFCControllerBase'





CLIENT_INTERFACES = dict(
    TASK = dict(FURL_FILE = 'ipcontroller-tc.furl'),
    MULTIENGINE = dict(FURLFILE='ipcontroller-mec.furl')
)

