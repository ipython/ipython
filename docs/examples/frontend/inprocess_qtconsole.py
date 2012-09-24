from IPython.inprocess.ipkernel import InProcessKernel
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.inprocess_kernelmanager import QtInProcessKernelManager
from IPython.lib import guisupport


def main():
    app = guisupport.get_app_qt4()

    # Create a kernel and populate the namespace.
    kernel = InProcessKernel()
    kernel.shell.push({'x': 0, 'y': 1, 'z': 2})

    # Create a kernel manager for the frontend and register it with the kernel.
    km = QtInProcessKernelManager(kernel=kernel)
    km.start_channels()
    kernel.frontends.append(km)

    # Create the Qt console frontend.
    control = RichIPythonWidget()
    control.exit_requested.connect(app.quit)
    control.kernel_manager = km
    control.show()

    # Execute some code directly. Note where the output appears.
    kernel.shell.run_cell('print "x=%r, y=%r, z=%r" % (x,y,z)')

    # Execute some code through the frontend (once the event loop is
    # running). Again, note where the output appears.
    do_later(control.execute, '%who')

    guisupport.start_event_loop_qt4(app)


def do_later(func, *args, **kwds):
    from IPython.external.qt import QtCore
    QtCore.QTimer.singleShot(0, lambda: func(*args, **kwds))


if __name__ == '__main__':
    main()
