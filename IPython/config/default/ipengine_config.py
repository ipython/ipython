c = get_config()

c.MPI.use = ''

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

c.Global.exec_lines = ['import numpy']

c.Global.log_dir_name = 'log'

c.Global.security_dir_name = 'security'

c.Global.log_level = 10

c.Global.shell_class = 'IPython.kernel.core.interpreter.Interpreter'

c.Global.furl_file_name = 'ipcontroller-engine.furl'

c.Global.furl_file = ''
