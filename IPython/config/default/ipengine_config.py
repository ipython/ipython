c = get_config()

c.MPI.default = 'mpi4py'

c.MPI.mpi4py = """from mpi4py import MPI as mpi
mpi.size = mpi.COMM_WORLD.Get_size()
mpi.rank = mpi.COMM_WORLD.Get_rank()
"""

c.MPI.pytrilinos = """from PyTrilinos import Epetra
class SimpleStruct:
pass
mpi = SimpleStruct()
mpi.rank = 0
mpi.size = 0
"""

c.Global.logfile = ''
c.Global.furl_file = 'ipcontroller-engine.furl'
