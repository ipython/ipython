from ..console.app import ZMQTerminalIPythonApp
from interactiveshell import GateOneInteractiveShell
import signal

from IPython.frontend.consoleapp import (
        IPythonConsoleApp, app_aliases, app_flags, aliases, app_aliases, flags
    )

class GateOneIPythonApp(ZMQTerminalIPythonApp):
    classes = [GateOneInteractiveShell] + IPythonConsoleApp.classes
    def _pylab_changed(self, name, old, new):
        pass
    
    def init_shell(self):
        IPythonConsoleApp.initialize(self)
        # relay sigint to kernel
        signal.signal(signal.SIGINT, self.handle_sigint)
        self.shell = GateOneInteractiveShell.instance(config=self.config,
                        display_banner=False, profile_dir=self.profile_dir,
                        ipython_dir=self.ipython_dir, kernel_manager=self.kernel_manager)


def launch_new_instance():
    """Create and run a full blown IPython instance"""
    app = GateOneIPythonApp.instance()
    app.initialize()
    app.start()

if __name__ == '__main__':
    launch_new_instance()
