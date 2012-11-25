from subprocess import Popen

from IPython.zmq.kernelmanager import KernelManager

def launch_ruby_kernel(fname='cf.json', **kw):
    cmd = ['iruby_ruby', '~/iruby/lib/kernel.rb', fname]
    cmd = ['/usr/local/Cellar/ruby/1.9.3-p286/bin/ruby',
            '/Users/matthiasbussonnier/iruby/lib/kernel.rb',
            fname]
            #~/.ipython/profile_default/security/kernel-10234.json
    return Popen(cmd)

class RubyKernelManager(KernelManager):
    def start_kernel(self, **kw):
        kw['launcher'] = launch_ruby_kernel
        return KernelManager.start_kernel(self, **kw)
