# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from frontend_widget import FrontendWidget


class IPythonWidget(FrontendWidget):
    """ A FrontendWidget for an IPython kernel.
    """

    #---------------------------------------------------------------------------
    # 'QObject' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, parent=None):
        super(IPythonWidget, self).__init__(parent)

        self._magic_overrides = {}

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' abstract interface
    #---------------------------------------------------------------------------

    def _execute(self, source, hidden):
        """ Reimplemented to override magic commands.
        """
        magic_source = source.strip()
        if magic_source.startswith('%'):
            magic_source = magic_source[1:]
        magic, sep, arguments = magic_source.partition(' ')
        if not magic:
            magic = magic_source

        callback = self._magic_overrides.get(magic)
        if callback:
            output = callback(arguments)
            if output:
                self.appendPlainText(output)
            self._show_prompt()
        else:
            super(IPythonWidget, self)._execute(source, hidden)

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------

    def execute_file(self, path, hidden=False):
        """ Reimplemented to use the 'run' magic.
        """
        self.execute('run %s' % path, hidden=hidden)

    #---------------------------------------------------------------------------
    # 'IPythonWidget' interface
    #---------------------------------------------------------------------------

    def set_magic_override(self, magic, callback):
        """ Overrides an IPython magic command. This magic will be intercepted
            by the frontend rather than passed on to the kernel and 'callback'
            will be called with a single argument: a string of argument(s) for
            the magic. The callback can (optionally) return text to print to the
            console.
        """
        self._magic_overrides[magic] = callback

    def remove_magic_override(self, magic):
        """ Removes the override for the specified magic, if there is one.
        """
        try:
            del self._magic_overrides[magic]
        except KeyError:
            pass


if __name__ == '__main__':
    from IPython.frontend.qt.kernelmanager import QtKernelManager

    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager.
    kernel_manager = QtKernelManager()
    kernel_manager.start_kernel()
    kernel_manager.start_listening()

    # Launch the application.
    app = QtGui.QApplication([])
    widget = IPythonWidget()
    widget.kernel_manager = kernel_manager
    widget.setWindowTitle('Python')
    widget.resize(640, 480)
    widget.show()
    app.exec_()
