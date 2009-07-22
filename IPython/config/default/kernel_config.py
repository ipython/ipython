from os.path import join
pjoin = join

from IPython.utils.genutils import get_ipython_dir, get_security_dir
security_dir = get_security_dir()


ENGINE_LOGFILE = ''

ENGINE_FURL_FILE = 'ipcontroller-engine.furl'

MPI_CONFIG_MPI4PY = """from mpi4py import MPI as mpi
mpi.size = mpi.COMM_WORLD.Get_size()
mpi.rank = mpi.COMM_WORLD.Get_rank()
"""

MPI_CONFIG_PYTRILINOS = """from PyTrilinos import Epetra
class SimpleStruct:
pass
mpi = SimpleStruct()
mpi.rank = 0
mpi.size = 0
"""

MPI_DEFAULT = ''

CONTROLLER_LOGFILE = ''
CONTROLLER_IMPORT_STATEMENT = ''
CONTROLLER_REUSE_FURLS = False

ENGINE_TUB_IP = ''
ENGINE_TUB_PORT = 0
ENGINE_TUB_LOCATION = ''
ENGINE_TUB_SECURE = True
ENGINE_TUB_CERT_FILE = 'ipcontroller-engine.pem'
ENGINE_FC_INTERFACE = 'IPython.kernel.enginefc.IFCControllerBase'
ENGINE_FURL_FILE = 'ipcontroller-engine.furl'

CONTROLLER_INTERFACES = dict(
    TASK = dict(
        CONTROLLER_INTERFACE = 'IPython.kernel.task.ITaskController',
        FC_INTERFACE = 'IPython.kernel.taskfc.IFCTaskController',
        FURL_FILE = pjoin(security_dir, 'ipcontroller-tc.furl')
    ),
    MULTIENGINE = dict(
        CONTROLLER_INTERFACE = 'IPython.kernel.multiengine.IMultiEngine',
        FC_INTERFACE = 'IPython.kernel.multienginefc.IFCSynchronousMultiEngine',
        FURL_FILE = pjoin(security_dir, 'ipcontroller-mec.furl')
    )
)

CLIENT_TUB_IP = ''
CLIENT_TUB_PORT = 0
CLIENT_TUB_LOCATION = ''
CLIENT_TUB_SECURE = True
CLIENT_TUB_CERT_FILE = 'ipcontroller-client.pem'

CLIENT_INTERFACES = dict(
    TASK = dict(FURL_FILE = 'ipcontroller-tc.furl'),
    MULTIENGINE = dict(FURLFILE='ipcontroller-mec.furl')
)

