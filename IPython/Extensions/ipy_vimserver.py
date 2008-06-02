""" Integration with gvim, by Erich Heine

Provides a %vim magic command, and reuses the same vim session. Uses 
unix domain sockets for communication between vim and IPython. ipy.vim is 
available in doc/examples of the IPython distribution.

Slightly touched up email announcement (and description how to use it) by 
Erich Heine is here:

Ive recently been playing with ipython, and like it quite a bit. I did
however discover a bit of frustration, namely with editor interaction.
I am a gvim user, and using the command edit on a new file causes
ipython to try and run that file as soon as the text editor opens
up. The -x command of course fixes this, but its still a bit annoying,
switching windows to do a run file, then back to the text
editor. Being a heavy tab user in gvim, another annoyance is not being
able to specify weather a new tab is how I choose to open the file.

Not being one to shirk my open source duties (and seeing this as a
good excuse to poke around ipython internals), Ive created a script
for having gvim and ipython work very nicely together. Ive attached
both to this email (hoping of course that the mailing list allows such
things).

There are 2 files: 

ipy_vimserver.py -- this file contains the ipython stuff
ipy.vim -- this file contains the gvim stuff

In combination they allow for a few functionalities:

#1. the vim magic command. This is a fancy wrapper around the edit
magic, that allows for a new option, -t, which opens the text in a new
gvim tab.  Otherwise it works the same as edit -x. (it internally
calls edit -x). This magic command also juggles vim server management,
so when it is called when there is not a gvim running, it creates a
new gvim instance, named after the ipython session name.  Once such a
gvim instance is running, it will be used for subsequent uses of the
vim command.

#2. ipython - gvim interaction. Once a file has been opened with the
vim magic (and a session set up, see below), pressing the F5 key in
vim will cause the calling ipython instance to execute run
filename.py. (if you typo like I do, this is very useful)

#3. ipython server - this is a thread wich listens on a unix domain
socket, and runs commands sent to that socket.

Note, this only works on POSIX systems, that allow for AF_UNIX type
sockets. It has only been tested on linux (a fairly recent debian
testing distro).

To install it put, the ipserver.py in your favorite locaion for
sourcing ipython scripts. I put the ipy.vim in
~/.vim/after/ftplugin/python/.

To use (this can be scripted im sure, but i usually have 2 or 3
ipythons and corresponding gvims open):

import ipy_vimserver
ipy_vimserver.setup('sessionname')

(Editors note - you can probably add these to your ipy_user_conf.py)

Then use ipython as you normally would, until you need to edit
something. Instead of edit, use the vim magic.  Thats it!

"""

import IPython.ipapi
#import ipythonhooks
import socket, select
import os, threading, subprocess
import re

ERRCONDS = select.POLLHUP|select.POLLERR
SERVER = None
ip = IPython.ipapi.get()

# this listens to a unix domain socket in a separate thread, so that comms
# between a vim instance and ipython can happen in a fun and productive way
class IpyServer(threading.Thread):
    def __init__(self, sname):
        super(IpyServer, self).__init__()
        self.keep_running = True
        self.__sname = sname
        self.socket = socket.socket(socket.AF_UNIX)
        self.poller = select.poll()
        self.current_conns = dict()
        self.setDaemon(True)

    def listen(self):
        self.socket.bind(self.__sname)
        self.socket.listen(1)

    def __handle_error(self, socket):
        if socket == self.socket.fileno():
            self.keep_running = False
            for a in self.current_conns.values():
                a.close()
            return False
        else:
            y = self.current_conns[socket]
            del self.current_conns[socket]
        y.close()
        self.poller.unregister(socket)

    def serve_me(self):
        self.listen()
        self.poller.register(self.socket,select.POLLIN|ERRCONDS)

        while self.keep_running:
            try:
                avail = self.poller.poll(1)
            except:
                continue

            if not avail: continue

            for sock, conds in avail:
                if conds & (ERRCONDS):
                    if self.__handle_error(sock): continue
                    else: break

                if sock == self.socket.fileno():
                    y = self.socket.accept()[0]
                    self.poller.register(y, select.POLLIN|ERRCONDS)
                    self.current_conns[y.fileno()] = y
                else: y = self.current_conns.get(sock)

                self.handle_request(y)

        os.remove(self.__sname)

    run = serve_me

    def stop(self):
        self.keep_running = False

    def handle_request(self,sock):
        sock.settimeout(1)
        while self.keep_running:
            try:
                x = sock.recv(4096)
            except socket.timeout:
                pass
            else:
                break
        self.do_it(x)

    def do_it(self, data):
        data = data.split('\n')
        cmds = list()
        for line in data:
            cmds.append(line)
        ip.runlines(cmds)


# try to help ensure that the unix domain socket is cleaned up proper
def shutdown_server(self):
    if SERVER:
        SERVER.stop()
        SERVER.join(3)
    raise IPython.ipapi.TryNext

ip.set_hook('shutdown_hook', shutdown_server, 10)

# this fun function exists to make setup easier for all, and makes the
# vimhook function ready for instance specific communication
def setup(sessionname='',socketdir=os.path.expanduser('~/.ipython/')):
    global SERVER

    if sessionname:
        session = sessionname
    elif os.environ.get('IPY_SESSION'):
        session = os.environ.get('IPY_SESSION')
    else:
        session = 'IPYS'
    vimhook.vimserver=session
    vimhook.ipyserver = os.path.join(socketdir, session)
    if not SERVER:
        SERVER = IpyServer(vimhook.ipyserver)
        SERVER.start()



# calls gvim, with all ops happening on the correct gvim instance for this
# ipython instance. it then calls edit -x (since gvim will return right away)
# things of note: it sets up a special environment, so that the ipy.vim script
# can connect back to the ipython instance and do fun things, like run the file
def vimhook(self, fname, line):
    env = os.environ.copy()
    vserver = vimhook.vimserver.upper()
    check = subprocess.Popen('gvim --serverlist', stdout = subprocess.PIPE,
        shell=True)
    check.wait()
    cval = [l for l in check.stdout.readlines() if vserver in l]

    if cval:
        vimargs = '--remote%s' % (vimhook.extras,)
    else:
        vimargs = ''
    vimhook.extras = ''

    env['IPY_SESSION'] = vimhook.vimserver
    env['IPY_SERVER'] = vimhook.ipyserver

    if line is None: line = ''
    else: line = '+' + line
    vim_cmd = 'gvim --servername %s %s %s %s' % (vimhook.vimserver, vimargs,
        line, fname)
    subprocess.call(vim_cmd, env=env, shell=True)


#default values to keep it sane...
vimhook.vimserver = ''
vimhook.ipyserver = ''

ip.set_hook('editor',vimhook)

# this is set up so more vim specific commands can be added, instead of just
# the current -t. all thats required is a compiled regex, a call to do_arg(pat)
# and the logic to deal with the new feature
newtab = re.compile(r'-t(?:\s|$)')
def vim(self, argstr):
    def do_arg(pat, rarg):
        x = len(pat.findall(argstr))
        if x:
            a = pat.sub('',argstr)
            return rarg, a
        else: return '', argstr

    t, argstr = do_arg(newtab, '-tab')
    vimhook.extras = t
    argstr = 'edit -x ' + argstr
    ip.magic(argstr)

ip.expose_magic('vim', vim)

