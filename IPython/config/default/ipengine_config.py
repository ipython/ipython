c = get_config()

c.MPI.use = 'mpi4py'

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

c.Global.log_to_file = False
c.Global.exec_lines = []
c.Global.log_dir_name = 'log'
c.Global.security_dir_name = 'security'
c.Global.shell_class = 'IPython.kernel.core.interpreter.Interpreter'
self.default_config.Global.furl_file_name = 'ipcontroller-engine.furl'
self.default_config.Global.furl_file = ''

