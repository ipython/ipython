""" A simple example of using the Qt console with an in-process kernel.

We shall see how to create the frontend widget, create an in-process kernel,
push Python objects into the kernel's namespace, and execute code in the
kernel, both directly and via the frontend widget.
"""

from IPython.kernel.inprocess.ipkernel import InProcessKernel
from IPython.frontend.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.frontend.qt.inprocess_kernelmanager import QtInProcessKernelManager
from IPython.lib import guisupport


def main():
    app = guisupport.get_app_qt4()

    # Create a kernel. 
    #
    # Setting the GUI is not necessary for the normal operation of the kernel,
    # but it is used for IPython GUI's integration, particularly in pylab. By
    # default, the inline backend is used, which is safe under all toolkits.
    #
    # WARNING: Under no circumstances should another GUI toolkit, like wx, be
    # used when running a Qt application. This will lead to unexpected behavior,
    # including segfaults.
    kernel = InProcessKernel(gui='qt4')

    # Populate the kernel's namespace.
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
