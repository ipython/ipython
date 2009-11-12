c = get_config()

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

# Start up messages are logged to stdout using the logging module.
# These all happen before the twisted reactor is started and are
# useful for debugging purposes. Can be (10=DEBUG,20=INFO,30=WARN,40=CRITICAL) 
# and smaller is more verbose.
# c.Global.log_level = 20

# Log to a file in cluster_dir/log, otherwise just log to sys.stdout.
# c.Global.log_to_file = False

# Remove old logs from cluster_dir/log before starting.
# c.Global.clean_logs = True

# A list of strings that will be executed in the users namespace on the engine
# before it connects to the controller.
# c.Global.exec_lines = ['import numpy']

# The engine will try to connect to the controller multiple times, to allow
# the controller time to startup and write its FURL file. These parameters 
# control the number of retries (connect_max_tries) and the initial delay
# (connect_delay) between attemps. The actual delay between attempts gets
# longer each time by a factor of 1.5 (delay[i] = 1.5*delay[i-1])
# those attemps.
# c.Global.connect_delay = 0.1
# c.Global.connect_max_tries = 15

# By default, the engine will look for the controller's FURL file in its own
# cluster directory. Sometimes, the FURL file will be elsewhere and this 
# attribute can be set to the full path of the FURL file.
# c.Global.furl_file = u''

# The working directory for the process. The application will use os.chdir
# to change to this directory before starting.
# c.Global.working_dir = os.getcwd()

#-----------------------------------------------------------------------------
# MPI configuration
#-----------------------------------------------------------------------------

# Upon starting the engine can be configured to call MPI_Init. This section
# configures that.

# Select which MPI section to execute to setup MPI. The value of this 
# attribute must match the name of another attribute in the MPI config 
# section (mpi4py, pytrilinos, etc.). This can also be set by the --mpi
# command line option.
# c.MPI.use = ''

# Initialize MPI using mpi4py. To use this, set c.MPI.use = 'mpi4py' to use
# --mpi=mpi4py at the command line.
# c.MPI.mpi4py = """from mpi4py import MPI as mpi
# mpi.size = mpi.COMM_WORLD.Get_size()
# mpi.rank = mpi.COMM_WORLD.Get_rank()
# """

# Initialize MPI using pytrilinos. To use this, set c.MPI.use = 'pytrilinos' 
# to use --mpi=pytrilinos at the command line.
# c.MPI.pytrilinos = """from PyTrilinos import Epetra
# class SimpleStruct:
# pass
# mpi = SimpleStruct()
# mpi.rank = 0
# mpi.size = 0
# """

#-----------------------------------------------------------------------------
# Developer level configuration attributes
#-----------------------------------------------------------------------------

# You shouldn't have to modify anything in this section. These attributes
# are more for developers who want to change the behavior of the controller
# at a fundamental level.

# You should not have to change these attributes.

# c.Global.shell_class = 'IPython.kernel.core.interpreter.Interpreter'

# c.Global.furl_file_name = u'ipcontroller-engine.furl'







