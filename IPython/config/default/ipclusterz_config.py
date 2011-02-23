import os

c = get_config()

#-----------------------------------------------------------------------------
# Select which launchers to use
#-----------------------------------------------------------------------------

# This allows you to control what method is used to start the controller
# and engines.  The following methods are currently supported:
# - Start as a regular process on localhost.
# - Start using mpiexec.
# - Start using the Windows HPC Server 2008 scheduler
# - Start using PBS
# - Start using SSH


# The selected launchers can be configured below.

# Options are:
# - LocalControllerLauncher
# - MPIExecControllerLauncher
# - PBSControllerLauncher
# - WindowsHPCControllerLauncher
# c.Global.controller_launcher = 'IPython.zmq.parallel.launcher.LocalControllerLauncher'

# Options are:
# - LocalEngineSetLauncher
# - MPIExecEngineSetLauncher
# - PBSEngineSetLauncher
# - WindowsHPCEngineSetLauncher
# c.Global.engine_launcher = 'IPython.zmq.parallel.launcher.LocalEngineSetLauncher'

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

# The default number of engines that will be started. This is overridden by
# the -n command line option: "ipcluster start -n 4"
# c.Global.n = 2

# Log to a file in cluster_dir/log, otherwise just log to sys.stdout.
# c.Global.log_to_file = False

# Remove old logs from cluster_dir/log before starting.
# c.Global.clean_logs = True

# The working directory for the process. The application will use os.chdir
# to change to this directory before starting.
# c.Global.work_dir = os.getcwd()


#-----------------------------------------------------------------------------
# Local process launchers
#-----------------------------------------------------------------------------

# The command line arguments to call the controller with.
# c.LocalControllerLauncher.controller_args = \
#    ['--log-to-file','--log-level', '40']

# The working directory for the controller
# c.LocalEngineSetLauncher.work_dir = u''

# Command line argument passed to the engines.
# c.LocalEngineSetLauncher.engine_args = ['--log-to-file','--log-level', '40']

#-----------------------------------------------------------------------------
# MPIExec launchers
#-----------------------------------------------------------------------------

# The mpiexec/mpirun command to use in started the controller.
# c.MPIExecControllerLauncher.mpi_cmd = ['mpiexec']

# Additional arguments to pass to the actual mpiexec command.
# c.MPIExecControllerLauncher.mpi_args = []

# The command line argument to call the controller with.
# c.MPIExecControllerLauncher.controller_args = \
#     ['--log-to-file','--log-level', '40']


# The mpiexec/mpirun command to use in started the controller.
# c.MPIExecEngineSetLauncher.mpi_cmd = ['mpiexec']

# Additional arguments to pass to the actual mpiexec command.
# c.MPIExecEngineSetLauncher.mpi_args = []

# Command line argument passed to the engines.
# c.MPIExecEngineSetLauncher.engine_args = ['--log-to-file','--log-level', '40']

# The default number of engines to start if not given elsewhere.
# c.MPIExecEngineSetLauncher.n = 1

#-----------------------------------------------------------------------------
# SSH launchers
#-----------------------------------------------------------------------------

# Todo


#-----------------------------------------------------------------------------
# Unix batch (PBS) schedulers launchers
#-----------------------------------------------------------------------------

# The command line program to use to submit a PBS job.
# c.PBSControllerLauncher.submit_command = 'qsub'

# The command line program to use to delete a PBS job.
# c.PBSControllerLauncher.delete_command = 'qdel'

# A regular expression that takes the output of qsub and find the job id.
# c.PBSControllerLauncher.job_id_regexp = r'\d+'

# The batch submission script used to start the controller. This is where
# environment variables would be setup, etc. This string is interpolated using
# the Itpl module in IPython.external. Basically, you can use ${n} for the
# number of engine and ${cluster_dir} for the cluster_dir.
# c.PBSControllerLauncher.batch_template = """"""

# The name of the instantiated batch script that will actually be used to
# submit the job. This will be written to the cluster directory.
# c.PBSControllerLauncher.batch_file_name = u'pbs_batch_script_controller'


# The command line program to use to submit a PBS job.
# c.PBSEngineSetLauncher.submit_command = 'qsub'

# The command line program to use to delete a PBS job.
# c.PBSEngineSetLauncher.delete_command = 'qdel'

# A regular expression that takes the output of qsub and find the job id.
# c.PBSEngineSetLauncher.job_id_regexp = r'\d+'

# The batch submission script used to start the engines. This is where
# environment variables would be setup, etc. This string is interpolated using
# the Itpl module in IPython.external. Basically, you can use ${n} for the
# number of engine and ${cluster_dir} for the cluster_dir.
# c.PBSEngineSetLauncher.batch_template = """"""

# The name of the instantiated batch script that will actually be used to
# submit the job. This will be written to the cluster directory.
# c.PBSEngineSetLauncher.batch_file_name = u'pbs_batch_script_engines'

#-----------------------------------------------------------------------------
# Windows HPC Server 2008 launcher configuration
#-----------------------------------------------------------------------------

# c.IPControllerJob.job_name = 'IPController'
# c.IPControllerJob.is_exclusive = False
# c.IPControllerJob.username = r'USERDOMAIN\USERNAME'
# c.IPControllerJob.priority = 'Highest'
# c.IPControllerJob.requested_nodes = ''
# c.IPControllerJob.project = 'MyProject'

# c.IPControllerTask.task_name = 'IPController'
# c.IPControllerTask.controller_cmd = [u'ipcontroller.exe']
# c.IPControllerTask.controller_args = ['--log-to-file', '--log-level', '40']
# c.IPControllerTask.environment_variables = {}

# c.WindowsHPCControllerLauncher.scheduler = 'HEADNODE'
# c.WindowsHPCControllerLauncher.job_file_name = u'ipcontroller_job.xml'


# c.IPEngineSetJob.job_name = 'IPEngineSet'
# c.IPEngineSetJob.is_exclusive = False
# c.IPEngineSetJob.username = r'USERDOMAIN\USERNAME'
# c.IPEngineSetJob.priority = 'Highest'
# c.IPEngineSetJob.requested_nodes = ''
# c.IPEngineSetJob.project = 'MyProject'

# c.IPEngineTask.task_name = 'IPEngine'
# c.IPEngineTask.engine_cmd = [u'ipengine.exe']
# c.IPEngineTask.engine_args = ['--log-to-file', '--log-level', '40']
# c.IPEngineTask.environment_variables = {}

# c.WindowsHPCEngineSetLauncher.scheduler = 'HEADNODE'
# c.WindowsHPCEngineSetLauncher.job_file_name = u'ipengineset_job.xml'







