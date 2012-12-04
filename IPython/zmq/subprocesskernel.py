#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------


from subprocess import Popen
from os.path import expanduser

from IPython.zmq.kernelmanager import KernelManager
from IPython.utils.traitlets import List
from IPython.config.configurable import Configurable


class SubprocessKernelManager(KernelManager, Configurable):

    kernel_launch_program = List(
        [],
        config=True,
        help="""the command to launch a foreing language kernel, use '{connexion_file_name}' to have
        the full path of the connexion file.
        """
    )

    def start_kernel(self, **kw):
        kw['launcher'] = self.launch_subprocess_kernel
        return KernelManager.start_kernel(self, **kw)

    def launch_subprocess_kernel(self, fname='cf.json', **kw):
        if not self.kernel_launch_program :
            raise ValueError("""kernel_launch program should be defined
            in config with the following form :

            c.SubprocessKernelManager.kernel_launch_program=['interpreter','program','{connexion_file_name}']
            """)
        cmd = [ expanduser(_.format(connexion_file_name=fname)) for _ in self.kernel_launch_program]
        return Popen(cmd)
