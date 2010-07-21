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
    
    def __init__(self, kernel_manager, parent=None):
        super(IPythonWidget, self).__init__(kernel_manager, parent)

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
    import sys
    from IPython.frontend.qt.kernelmanager import QtKernelManager

    # Create KernelManager
    xreq_addr = ('127.0.0.1', 5575)
    sub_addr = ('127.0.0.1', 5576)
    rep_addr = ('127.0.0.1', 5577)
    kernel_manager = QtKernelManager(xreq_addr, sub_addr, rep_addr)
    kernel_manager.sub_channel.start()
    kernel_manager.xreq_channel.start()

    # Launch application
    app = QtGui.QApplication(sys.argv)
    widget = IPythonWidget(kernel_manager)
    widget.setWindowTitle('Python')
    widget.resize(640, 480)
    widget.show()
    sys.exit(app.exec_())
    
