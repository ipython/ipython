from subprocess import Popen

from IPython.zmq.kernelmanager import KernelManager
from IPython.utils.traitlets import Unicode


class SubprocessKernelManager(KernelManager):

    kernel_launch_command = Unicode(
        'echo "this is not configurated"',
        config=True,
        help="""the command to launch a foreing language kernel, use %(cfile) to have 
        the full path of the connexion file.
        """
    )

    def start_kernel(self, **kw):
        kw['launcher'] = self.launch_ruby_kernel
        return KernelManager.start_kernel(self, **kw)

    def launch_ruby_kernel(self, fname='cf.json', **kw):
        cmd = ['/usr/local/Cellar/ruby/1.9.3-p286/bin/ruby',
                '/Users/matthiasbussonnier/iruby/lib/kernel.rb',
                fname]
                #~/.ipython/profile_default/security/kernel-10234.json
        return Popen(cmd)
