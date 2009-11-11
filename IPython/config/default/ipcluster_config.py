import os

c = get_config()

#-----------------------------------------------------------------------------
# Select which launchers to use
#-----------------------------------------------------------------------------

# This allows you to control what method is used to start the controller
# and engines.  The following methods are currently supported:
# * Start as a regular process on localhost.
# * Start using mpiexec.
# * Start using PBS
# * Start using SSH (currently broken)

# The selected launchers can be configured below.

# Options are (LocalControllerLauncher, MPIExecControllerLauncher,
# PBSControllerLauncher, WindowsHPCControllerLauncher)
# c.Global.controller_launcher = 'IPython.kernel.launcher.LocalControllerLauncher'

# Options are (LocalEngineSetLauncher, MPIExecEngineSetLauncher,
# PBSEngineSetLauncher)
# c.Global.engine_launcher = 'IPython.kernel.launcher.LocalEngineSetLauncher'

#-----------------------------------------------------------------------------
# Global configuration
#-----------------------------------------------------------------------------

# The default number of engine that will be started. This is overridden by
# the -n command line option: "ipcluster start -n 4"
# c.Global.n = 2

# Log to a file in cluster_dir/log, otherwise just log to sys.stdout.
# c.Global.log_to_file = False

# Remove old logs from cluster_dir/log before starting.
# c.Global.clean_logs = True

#-----------------------------------------------------------------------------
# Controller launcher configuration
#-----------------------------------------------------------------------------

# Configure how the controller is started. The configuration of the controller
# can also bet setup by editing the controller config file: 
# ipcontroller_config.py

# The command line arguments to call the controller with.
# c.LocalControllerLauncher.controller_args = \
#    ['--log-to-file','--log-level', '40']

# The mpiexec/mpirun command to use in started the controller.
# c.MPIExecControllerLauncher.mpi_cmd = ['mpiexec']

# Additional arguments to pass to the actual mpiexec command.
# c.MPIExecControllerLauncher.mpi_args = []

# The command line argument to call the controller with.
# c.MPIExecControllerLauncher.controller_args = \
#     ['--log-to-file','--log-level', '40']

# The command line program to use to submit a PBS job.
# c.PBSControllerLauncher.submit_command = 'qsub'

# The command line program to use to delete a PBS job.
# c.PBSControllerLauncher.delete_command = 'qdel'

# A regular expression that takes the output of qsub and find the job id.
# c.PBSControllerLauncher.job_id_regexp = '\d+'

# The batch submission script used to start the controller. This is where
# environment variables would be setup, etc. This string is interpolated using
# the Itpl module in IPython.external. Basically, you can use ${profile} for 
# the controller profile or ${cluster_dir} for the cluster_dir.
# c.PBSControllerLauncher.batch_template = """"""

# The name of the instantiated batch script that will actually be used to
# submit the job. This will be written to the cluster directory.
# c.PBSControllerLauncher.batch_file_name = u'pbs_batch_script_controller'

#-----------------------------------------------------------------------------
# Windows HPC Server 2008 launcher configuration
#-----------------------------------------------------------------------------

# c.WinHPCJob.username = 'DOMAIN\\user'
# c.WinHPCJob.priority = 'Highest'
# c.WinHPCJob.requested_nodes = ''
# c.WinHPCJob.project = ''
# c.WinHPCJob.is_exclusive = False

# c.WinHPCTask.environment_variables = {}
# c.WinHPCTask.work_directory = ''
# c.WinHPCTask.is_rerunnable = True

# c.IPControllerTask.task_name = 'IPController'
# c.IPControllerTask.controller_cmd = ['ipcontroller.exe']
# c.IPControllerTask.controller_args = ['--log-to-file', '--log-level', '40']
# c.IPControllerTask.environment_variables = {}

# c.IPEngineTask.task_name = 'IPController'
# c.IPEngineTask.engine_cmd = ['ipengine.exe']
# c.IPEngineTask.engine_args = ['--log-to-file', '--log-level', '40']
# c.IPEngineTask.environment_variables = {}

# c.WindowsHPCLauncher.scheduler = 'HEADNODE'
# c.WindowsHPCLauncher.username = '\\DOMAIN\USERNAME'
# c.WindowsHPCLauncher.priority = 'Highest'
# c.WindowsHPCLauncher.requested_nodes = ''
# c.WindowsHPCLauncher.job_file_name = u'ipython_job.xml'
# c.WindowsHPCLauncher.project = 'MyProject'

# c.WindowsHPCControllerLauncher.scheduler = 'HEADNODE'
# c.WindowsHPCControllerLauncher.username = '\\DOMAIN\USERNAME'
# c.WindowsHPCControllerLauncher.priority = 'Highest'
# c.WindowsHPCControllerLauncher.requested_nodes = ''
# c.WindowsHPCControllerLauncher.job_file_name = u'ipcontroller_job.xml'
# c.WindowsHPCControllerLauncher.project = 'MyProject'


#-----------------------------------------------------------------------------
# Engine launcher configuration
#-----------------------------------------------------------------------------

# Command line argument passed to the engines.
# c.LocalEngineSetLauncher.engine_args = ['--log-to-file','--log-level', '40']

# The mpiexec/mpirun command to use in started the controller.
# c.MPIExecEngineSetLauncher.mpi_cmd = ['mpiexec']

# Additional arguments to pass to the actual mpiexec command.
# c.MPIExecEngineSetLauncher.mpi_args = []

# Command line argument passed to the engines.
# c.MPIExecEngineSetLauncher.engine_args = ['--log-to-file','--log-level', '40']

# The default number of engines to start if not given elsewhere.
# c.MPIExecEngineSetLauncher.n = 1

# The command line program to use to submit a PBS job.
# c.PBSEngineSetLauncher.submit_command = 'qsub'

# The command line program to use to delete a PBS job.
# c.PBSEngineSetLauncher.delete_command = 'qdel'

# A regular expression that takes the output of qsub and find the job id.
# c.PBSEngineSetLauncher.job_id_regexp = '\d+'

# The batch submission script used to start the engines. This is where
# environment variables would be setup, etc. This string is interpolated using
# the Itpl module in IPython.external. Basically, you can use ${n} for the
# number of engine, ${profile} or the engine profile and ${cluster_dir} 
# for the cluster_dir.
# c.PBSEngineSetLauncher.batch_template = """"""

# The name of the instantiated batch script that will actually be used to
# submit the job. This will be written to the cluster directory.
# c.PBSEngineSetLauncher.batch_file_name = u'pbs_batch_script_engines'

#-----------------------------------------------------------------------------
# Base launcher configuration
#-----------------------------------------------------------------------------

# The various launchers are organized into an inheritance hierarchy. 
# The configurations can also be iherited and the following attributes 
# allow you to configure the base classes.

# c.MPIExecLauncher.mpi_cmd = ['mpiexec']
# c.MPIExecLauncher.mpi_args = []
# c.MPIExecLauncher.program = []
# c.MPIExecLauncher.program_args = []
# c.MPIExecLauncher.n = 1

# c.SSHLauncher.ssh_cmd = ['ssh']
# c.SSHLauncher.ssh_args = []
# c.SSHLauncher.program = []
# s.SSHLauncher.program_args = []
# c.SSHLauncher.hostname = ''
# c.SSHLauncher.user = os.environ['USER']

# c.BatchSystemLauncher.submit_command
# c.BatchSystemLauncher.delete_command
# c.BatchSystemLauncher.job_id_regexp
# c.BatchSystemLauncher.batch_template
# c.BatchSystemLauncher.batch_file_name

# c.PBSLauncher.submit_command = 'qsub'
# c.PBSLauncher.delete_command = 'qdel'
# c.PBSLauncher.job_id_regexp = '\d+'
# c.PBSLauncher.batch_template = """"""
# c.PBSLauncher.batch_file_name = u'pbs_batch_script'




