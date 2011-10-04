""" Simple TCP socket server that executes statements in IPython instance.

Usage:

import ipy_server
ipy_server.serve_thread(16455)

Now, to execute the statements in this ipython instance, open a TCP socket
(port 16455), write out the statements, and close the socket.
You can use e.g. "telnet localhost 16455" or a script to do this.

This is a bit like 'M-x server-start" or gnuserv in the emacs world.

"""

from IPython.core import ipapi
ip = ipapi.get()

import SocketServer

# user-accessible port
PORT = 8099

class IPythonRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        #print "connection from", self.client_address
        inp = self.rfile.read().replace('\r\n','\n')
        #print "Execute",inp
        ip.runlines(inp)

def serve(port = PORT):
    server = SocketServer.TCPServer(("", port), IPythonRequestHandler)
    print "ipy_server on TCP port", port
    server.serve_forever()

def serve_thread(port = PORT):
    import thread
    thread.start_new_thread(serve, (port,))