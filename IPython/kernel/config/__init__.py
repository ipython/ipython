# encoding: utf-8

"""Default kernel configuration."""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

from os.path import join as pjoin

from IPython.external.configobj import ConfigObj
from IPython.config.api import ConfigObjManager
from IPython.genutils import get_ipython_dir, get_security_dir

default_kernel_config = ConfigObj()

security_dir = get_security_dir()

#-------------------------------------------------------------------------------
# Engine Configuration
#-------------------------------------------------------------------------------

engine_config = dict(
    logfile = '',    # Empty means log to stdout
    furl_file = pjoin(security_dir, 'ipcontroller-engine.furl')
)

#-------------------------------------------------------------------------------
# MPI Configuration
#-------------------------------------------------------------------------------

mpi_config = dict(
    mpi4py = """from mpi4py import MPI as mpi
mpi.size = mpi.COMM_WORLD.Get_size()
mpi.rank = mpi.COMM_WORLD.Get_rank()
""",
    pytrilinos = """from PyTrilinos import Epetra
class SimpleStruct:
    pass
mpi = SimpleStruct()
mpi.rank = 0
mpi.size = 0
""",
    default = ''
)

#-------------------------------------------------------------------------------
# Controller Configuration
#-------------------------------------------------------------------------------

controller_config = dict(

    logfile = '',    # Empty means log to stdout
    import_statement = '',

    engine_tub = dict(
        ip = '',         # Empty string means all interfaces
        port = 0,        # 0 means pick a port for me
        location = '',    # Empty string means try to set automatically
        secure = True,
        cert_file = pjoin(security_dir, 'ipcontroller-engine.pem'),
    ),
    engine_fc_interface = 'IPython.kernel.enginefc.IFCControllerBase',
    engine_furl_file = pjoin(security_dir, 'ipcontroller-engine.furl'),
    
    controller_interfaces = dict(
        # multiengine = dict(
        #     controller_interface = 'IPython.kernel.multiengine.IMultiEngine',
        #     fc_interface = 'IPython.kernel.multienginefc.IFCMultiEngine',
        #     furl_file = 'ipcontroller-mec.furl'
        # ),
        task = dict(
            controller_interface = 'IPython.kernel.task.ITaskController',
            fc_interface = 'IPython.kernel.taskfc.IFCTaskController',
            furl_file = pjoin(security_dir, 'ipcontroller-tc.furl')
        ),
        multiengine = dict(
            controller_interface = 'IPython.kernel.multiengine.IMultiEngine',
            fc_interface = 'IPython.kernel.multienginefc.IFCSynchronousMultiEngine',
            furl_file = pjoin(security_dir, 'ipcontroller-mec.furl')
        )
    ),

    client_tub = dict(
        ip = '',         # Empty string means all interfaces
        port = 0,        # 0 means pick a port for me
        location = '',    # Empty string means try to set automatically
        secure = True,
        cert_file = pjoin(security_dir, 'ipcontroller-client.pem')
    )
)

#-------------------------------------------------------------------------------
# Client Configuration
#-------------------------------------------------------------------------------

client_config = dict(
    client_interfaces = dict(
        task = dict(
            furl_file = pjoin(security_dir, 'ipcontroller-tc.furl')
        ),
        multiengine = dict(
            furl_file = pjoin(security_dir, 'ipcontroller-mec.furl')
        )
    )
)

default_kernel_config['engine'] = engine_config
default_kernel_config['mpi'] = mpi_config
default_kernel_config['controller'] = controller_config
default_kernel_config['client'] = client_config


config_manager = ConfigObjManager(default_kernel_config, 'IPython.kernel.ini')