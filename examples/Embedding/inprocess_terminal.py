from __future__ import print_function
import os

from IPython.kernel.inprocess import InProcessKernelManager
from IPython.terminal.console.interactiveshell import ZMQTerminalInteractiveShell


def print_process_id():
    print('Process ID is:', os.getpid())


def main():
    print_process_id()

    # Create an in-process kernel
    # >>> print_process_id()
    # will print the same process ID as the main process
    kernel_manager = InProcessKernelManager()
    kernel_manager.start_kernel()
    kernel = kernel_manager.kernel
    kernel.gui = 'qt4'
    kernel.shell.push({'foo': 43, 'print_process_id': print_process_id})
    client = kernel_manager.client()
    client.start_channels()

    shell = ZMQTerminalInteractiveShell(manager=kernel_manager, client=client)
    shell.mainloop()


if __name__ == '__main__':
    main()
