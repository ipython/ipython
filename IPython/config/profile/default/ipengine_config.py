c = get_config()

#-----------------------------------------------------------------------------
# Application configuration
#-----------------------------------------------------------------------------
app = c.IPEngineApp

# Start up messages are logged to stdout using the logging module.
# These all happen before the twisted reactor is started and are
# useful for debugging purposes. Can be (10=DEBUG,20=INFO,30=WARN,40=CRITICAL) 
# and smaller is more verbose.
# app.log_level = 20

# Log to a file in cluster_dir/log, otherwise just log to sys.stdout.
# app.log_to_file = False

# Remove old logs from cluster_dir/log before starting.
# app.clean_logs = True

# A list of strings that will be executed in the users namespace on the engine
# before it connects to the controller.
# app.exec_lines = ['import numpy']

# The engine will try to connect to the controller multiple times, to allow
# the controller time to startup and write its FURL file. These parameters 
# control the number of retries (connect_max_tries) and the initial delay
# (connect_delay) between attemps. The actual delay between attempts gets
# longer each time by a factor of 1.5 (delay[i] = 1.5*delay[i-1])
# those attemps.
# app.connect_delay = 0.1
# app.connect_max_tries = 15

# By default, the engine will look for the controller's JSON file in its own
# cluster directory. Sometimes, the JSON file will be elsewhere and this 
# attribute can be set to the full path of the JSON file.
# app.url_file = u'/path/to/my/ipcontroller-engine.json'

# The working directory for the process. The application will use os.chdir
# to change to this directory before starting.
# app.work_dir = os.getcwd()

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

# app.url_file_name = u'ipcontroller-engine.furl'




