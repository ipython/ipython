# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from frontend_widget import FrontendWidget


class IPythonWidget(FrontendWidget):
    """ A FrontendWidget for an IPython kernel.
    """

    #---------------------------------------------------------------------------
    # 'FrontendWidget' interface
    #---------------------------------------------------------------------------
    
    def __init__(self, parent=None):
        super(IPythonWidget, self).__init__(parent)

        self._magic_overrides = {}

    def execute_source(self, source, hidden=False, interactive=False):
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
            self._show_prompt('>>> ')
            return True
        else:
            return super(IPythonWidget, self).execute_source(source, hidden,
                                                             interactive)

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
    from IPython.external.argparse import ArgumentParser
    from IPython.frontend.qt.kernelmanager import QtKernelManager

    # Don't let Qt swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Parse command line arguments.
    parser = ArgumentParser()
    parser.add_argument('--ip', type=str, default='127.0.0.1',
                        help='set the kernel\'s IP address [default localhost]')
    parser.add_argument('--xreq', type=int, metavar='PORT', default=5575,
                        help='set the XREQ Channel port [default %(default)i]')
    parser.add_argument('--sub', type=int, metavar='PORT', default=5576,
                        help='set the SUB Channel port [default %(default)i]')
    namespace = parser.parse_args()

    # Create KernelManager
    ip = namespace.ip
    kernel_manager = QtKernelManager(xreq_address = (ip, namespace.xreq),
                                     sub_address = (ip, namespace.sub))
    kernel_manager.start_listening()

    # Launch application
    app = QtGui.QApplication([])
    widget = IPythonWidget()
    widget.kernel_manager = kernel_manager
    widget.setWindowTitle('Python')
    widget.resize(640, 480)
    widget.show()
    app.exec_()
    
