""" A minimal application using the Qt console-style IPython frontend.
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# Local imports
import os
from IPython.external.argparse import ArgumentParser
from IPython.frontend.html.kernelmanager import HttpKernelManager, \
    IPyHttpServer, IPyHttpHandler

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

LOCALHOST = '127.0.0.1'

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------

def main():
    """ Entry point for application.
    """
    # Parse command line arguments.
    parser = ArgumentParser()
    kgroup = parser.add_argument_group('kernel options')
    kgroup.add_argument('-e', '--existing', action='store_true',
                        help='connect to an existing kernel')
    kgroup.add_argument('--ip', type=str, default=LOCALHOST,
                        help='set the kernel\'s IP address [default localhost]')
    kgroup.add_argument('--xreq', type=int, metavar='PORT', default=0,
                        help='set the XREQ channel port [default random]')
    kgroup.add_argument('--sub', type=int, metavar='PORT', default=0,
                        help='set the SUB channel port [default random]')
    kgroup.add_argument('--rep', type=int, metavar='PORT', default=0,
                        help='set the REP channel port [default random]')
    kgroup.add_argument('--hb', type=int, metavar='PORT', default=0,
                        help='set the heartbeat port [default: random]')

    egroup = kgroup.add_mutually_exclusive_group()
    egroup.add_argument('--pure', action='store_true', help = \
                        'use a pure Python kernel instead of an IPython kernel')
    egroup.add_argument('--pylab', type=str, metavar='GUI', nargs='?', 
                       const='auto', help = \
        "Pre-load matplotlib and numpy for interactive use. If GUI is not \
         given, the GUI backend is matplotlib's, otherwise use one of: \
         ['tk', 'gtk', 'qt', 'wx', 'inline'].")

    wgroup = parser.add_argument_group('widget options')
    wgroup.add_argument('--paging', type=str, default='inside',
                        choices = ['inside', 'hsplit', 'vsplit', 'none'],
                        help='set the paging style [default inside]')
    wgroup.add_argument('--rich', action='store_true',
                        help='enable rich text support')
    wgroup.add_argument('--gui-completion', action='store_true',
                        help='use a GUI widget for tab completion')

    args = parser.parse_args()

    # Don't let Qt or ZMQ swallow KeyboardInterupts.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    # Create a KernelManager and start a kernel.
    kernel_manager = HttpKernelManager(xreq_address=(args.ip, args.xreq),
                                     sub_address=(args.ip, args.sub),
                                     rep_address=(args.ip, args.rep),
                                     hb_address=(args.ip, args.hb))
    if args.ip == LOCALHOST and not args.existing:
        if args.pure:
            kernel_manager.start_kernel(ipython=False)
        elif args.pylab:
            kernel_manager.start_kernel(pylab=args.pylab)
        else:
            kernel_manager.start_kernel()
    kernel_manager.start_channels()
    
    #Start the web server
#    os.system("xdg-open http://localhost:8080/notebook")
    server = IPyHttpServer(("", 8080), IPyHttpHandler)
    server.serve_forever()

if __name__ == '__main__':
    main()
