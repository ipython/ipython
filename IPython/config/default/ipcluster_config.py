import os

c = get_config()

# Options are:
# * LocalControllerLauncher
# * PBSControllerLauncher
# c.Global.controller_launcher = 'IPython.kernel.launcher.LocalControllerLauncher'

# Options are:
# * LocalEngineSetLauncher
# * MPIExecEngineSetLauncher
# * PBSEngineSetLauncher
# c.Global.engine_launcher = 'IPython.kernel.launcher.LocalEngineSetLauncher'

# c.Global.log_to_file = False
# c.Global.n = 2
# c.Global.reset_config = False

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

# c.PBSLauncher.submit_command = 'qsub'
# c.PBSLauncher.delete_command = 'qdel'
# c.PBSLauncher.job_id_regexp = '\d+'
# c.PBSLauncher.batch_template = """"""
# c.PBSLauncher.batch_file_name = u'pbs_batch_script'

# c.LocalControllerLauncher.controller_args = []

# c.MPIExecControllerLauncher.mpi_cmd = ['mpiexec']
# c.MPIExecControllerLauncher.mpi_args = []
# c.MPIExecControllerLauncher.controller_args = []
# c.MPIExecControllerLauncher.n = 1

# c.PBSControllerLauncher.submit_command = 'qsub'
# c.PBSControllerLauncher.delete_command = 'qdel'
# c.PBSControllerLauncher.job_id_regexp = '\d+'
# c.PBSControllerLauncher.batch_template = """"""
# c.PBSLauncher.batch_file_name = u'pbs_batch_script'

# c.LocalEngineLauncher.engine_args = []

# c.LocalEngineSetLauncher.engine_args = []

# c.MPIExecEngineSetLauncher.mpi_cmd = ['mpiexec']
# c.MPIExecEngineSetLauncher.mpi_args = []
# c.MPIExecEngineSetLauncher.controller_args = []
# c.MPIExecEngineSetLauncher.n = 1

# c.PBSEngineSetLauncher.submit_command = 'qsub'
# c.PBSEngineSetLauncher.delete_command = 'qdel'
# c.PBSEngineSetLauncher.job_id_regexp = '\d+'
# c.PBSEngineSetLauncher.batch_template = """"""
# c.PBSEngineSetLauncher.batch_file_name = u'pbs_batch_script'

