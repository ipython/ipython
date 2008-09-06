#!/usr/bin/env python
# encoding: utf-8

"""Start an IPython cluster conveniently, either locally or remotely.

Basic usage
-----------

For local operation, the simplest mode of usage is:

  %prog -n N

where N is the number of engines you want started.

For remote operation, you must call it with a cluster description file:

  %prog -f clusterfile.py

The cluster file is a normal Python script which gets run via execfile().  You
can have arbitrary logic in it, but all that matters is that at the end of the
execution, it declares the variables 'controller', 'engines', and optionally
'sshx'.  See the accompanying examples for details on what these variables must
contain.


Notes
-----

WARNING: this code is still UNFINISHED and EXPERIMENTAL!  It is incomplete,
some listed options are not really implemented, and all of its interfaces are
subject to change.

When operating over SSH for a remote cluster, this program relies on the
existence of a particular script called 'sshx'.  This script must live in the
target systems where you'll be running your controller and engines, and is
needed to configure your PATH and PYTHONPATH variables for further execution of
python code at the other end of an SSH connection.  The script can be as simple
as:

#!/bin/sh
. $HOME/.bashrc
"$@"

which is the default one provided by IPython.  You can modify this or provide
your own.  Since it's quite likely that for different clusters you may need
this script to configure things differently or that it may live in different
locations, its full path can be set in the same file where you define the
cluster setup.  IPython's order of evaluation for this variable is the
following:

  a) Internal default: 'sshx'.  This only works if it is in the default system
  path which SSH sets up in non-interactive mode.

  b) Environment variable: if $IPYTHON_SSHX is defined, this overrides the
  internal default.

  c) Variable 'sshx' in the cluster configuration file: finally, this will
  override the previous two values.
 
This code is Unix-only, with precious little hope of any of this ever working
under Windows, since we need SSH from the ground up, we background processes,
etc.  Ports of this functionality to Windows are welcome.


Call summary
------------

    %prog [options]
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Stdlib imports
#-------------------------------------------------------------------------------

import os
import signal
import sys
import time

from optparse import OptionParser
from subprocess import Popen,call

#---------------------------------------------------------------------------
# IPython imports
#---------------------------------------------------------------------------
from IPython.tools import utils
from IPython.genutils import get_ipython_dir

#---------------------------------------------------------------------------
# Normal code begins
#---------------------------------------------------------------------------

def parse_args():
    """Parse command line and return opts,args."""

    parser = OptionParser(usage=__doc__)
    newopt = parser.add_option  # shorthand

    newopt("--controller-port", type="int", dest="controllerport",
           help="the TCP port the controller is listening on")

    newopt("--controller-ip", type="string", dest="controllerip",
           help="the TCP ip address of the controller")

    newopt("-n", "--num", type="int", dest="n",default=2,
           help="the number of engines to start")

    newopt("--engine-port", type="int", dest="engineport",
           help="the TCP port the controller will listen on for engine "
           "connections")
    
    newopt("--engine-ip", type="string", dest="engineip",
           help="the TCP ip address the controller will listen on "
           "for engine connections")

    newopt("--mpi", type="string", dest="mpi",
           help="use mpi with package:  for instance --mpi=mpi4py")
    
    newopt("-l", "--logfile", type="string", dest="logfile",
           help="log file name")

    newopt('-f','--cluster-file',dest='clusterfile',
           help='file describing a remote cluster')

    return parser.parse_args()

def numAlive(controller,engines):
    """Return the number of processes still alive."""
    retcodes = [controller.poll()] + \
               [e.poll() for e in engines]
    return retcodes.count(None)

stop = lambda pid: os.kill(pid,signal.SIGINT)
kill = lambda pid: os.kill(pid,signal.SIGTERM)

def cleanup(clean,controller,engines):
    """Stop the controller and engines with the given cleanup method."""
    
    for e in engines:
        if e.poll() is None:
            print 'Stopping engine, pid',e.pid
            clean(e.pid)
    if controller.poll() is None:
        print 'Stopping controller, pid',controller.pid
        clean(controller.pid)


def ensureDir(path):
    """Ensure a directory exists or raise an exception."""
    if not os.path.isdir(path):
        os.makedirs(path)


def startMsg(control_host,control_port=10105):
    """Print a startup message"""
    print
    print 'Your cluster is up and running.'
    print
    print 'For interactive use, you can make a MultiEngineClient with:'
    print
    print 'from IPython.kernel import client'
    print "mec = client.MultiEngineClient()"
    print
    print 'You can then cleanly stop the cluster from IPython using:'
    print
    print 'mec.kill(controller=True)'
    print

    
def clusterLocal(opt,arg):
    """Start a cluster on the local machine."""
    
    # Store all logs inside the ipython directory
    ipdir = get_ipython_dir()
    pjoin = os.path.join

    logfile = opt.logfile
    if logfile is None:
        logdir_base = pjoin(ipdir,'log')
        ensureDir(logdir_base)
        logfile = pjoin(logdir_base,'ipcluster-')

    print 'Starting controller:',
    controller = Popen(['ipcontroller','--logfile',logfile,'-x','-y'])
    print 'Controller PID:',controller.pid

    print 'Starting engines:   ',
    time.sleep(5)

    englogfile = '%s%s-' % (logfile,controller.pid)
    mpi = opt.mpi
    if mpi: # start with mpi - killing the engines with sigterm will not work if you do this
        engines = [Popen(['mpirun', '-np', str(opt.n), 'ipengine', '--mpi', 
            mpi, '--logfile',englogfile])]
        # engines = [Popen(['mpirun', '-np', str(opt.n), 'ipengine', '--mpi', mpi])]
    else: # do what we would normally do
        engines = [ Popen(['ipengine','--logfile',englogfile])
                    for i in range(opt.n) ]
    eids = [e.pid for e in engines]
    print 'Engines PIDs:  ',eids
    print 'Log files: %s*' % englogfile
    
    proc_ids = eids + [controller.pid]
    procs = engines + [controller]

    grpid = os.getpgrp()
    try:
        startMsg('127.0.0.1')
        print 'You can also hit Ctrl-C to stop it, or use from the cmd line:'
        print
        print 'kill -INT',grpid
        print
        try:
            while True:
                time.sleep(5)
        except:
            pass
    finally:
        print 'Stopping cluster.  Cleaning up...'
        cleanup(stop,controller,engines)
        for i in range(4):
            time.sleep(i+2)
            nZombies = numAlive(controller,engines)
            if  nZombies== 0:
                print 'OK: All processes cleaned up.'
                break
            print 'Trying again, %d processes did not stop...' % nZombies
            cleanup(kill,controller,engines)
            if numAlive(controller,engines) == 0:
                print 'OK: All processes cleaned up.'
                break
        else:
            print '*'*75
            print 'ERROR: could not kill some processes, try to do it',
            print 'manually.'
            zombies = []
            if controller.returncode is None:
                print 'Controller is alive: pid =',controller.pid
                zombies.append(controller.pid)
            liveEngines = [ e for e in engines if e.returncode is None ]
            for e in liveEngines:
                print 'Engine is alive:     pid =',e.pid
                zombies.append(e.pid)
            print
            print 'Zombie summary:',' '.join(map(str,zombies))

def clusterRemote(opt,arg):
    """Start a remote cluster over SSH"""

    # B. Granger, 9/3/08
    # The launching of a remote cluster using SSH and a clusterfile
    # is broken.  Because it won't be fixed before the 0.9 release, 
    # we are removing it.  For now, we just print a message to the 
    # user and abort.
    
    print """The launching of a remote IPython cluster using SSL
and a clusterfile has been removed in this release.  
It has been broken for a while and we are in the process 
of building a new process management system that will be 
used to provide a more robust way of starting an IPython
cluster.

For now remote clusters have to be launched using ipcontroller
and ipengine separately.
    """
    sys.exit(1)

    # Load the remote cluster configuration
    clConfig = {}
    execfile(opt.clusterfile,clConfig)
    contConfig = clConfig['controller']
    engConfig = clConfig['engines']
    # Determine where to find sshx:
    sshx = clConfig.get('sshx',os.environ.get('IPYTHON_SSHX','sshx'))
    
    # Store all logs inside the ipython directory
    ipdir = get_ipython_dir()
    pjoin = os.path.join

    logfile = opt.logfile
    if logfile is None:
        logdir_base = pjoin(ipdir,'log')
        ensureDir(logdir_base)
        logfile = pjoin(logdir_base,'ipcluster')

    # Append this script's PID to the logfile name always
    logfile = '%s-%s' % (logfile,os.getpid())
    
    print 'Starting controller:'
    # Controller data:
    xsys = os.system

    contHost = contConfig['host']
    contLog = '%s-con-%s-' % (logfile,contHost)
    cmd = "ssh %s '%s' 'ipcontroller --logfile %s' &" % \
          (contHost,sshx,contLog)
    #print 'cmd:<%s>' % cmd  # dbg
    xsys(cmd)
    time.sleep(2)

    print 'Starting engines:   '
    for engineHost,engineData in engConfig.iteritems():
        if isinstance(engineData,int):
            numEngines = engineData
        else:
            raise NotImplementedError('port configuration not finished for engines')

        print 'Sarting %d engines on %s' % (numEngines,engineHost)
        engLog = '%s-eng-%s-' % (logfile,engineHost)
        for i in range(numEngines):
            cmd = "ssh %s '%s' 'ipengine --controller-ip %s --logfile %s' &" % \
                      (engineHost,sshx,contHost,engLog)
            #print 'cmd:<%s>' % cmd  # dbg
            xsys(cmd)
        # Wait after each host a little bit
        time.sleep(1)
            
    startMsg(contConfig['host'])
        
def main():
    """Main driver for the two big options: local or remote cluster."""
    
    if sys.platform=='win32':
        print """ipcluster does not work on Microsoft Windows.  Please start
your IPython cluster using the ipcontroller and ipengine scripts."""
        sys.exit(1)
    
    opt,arg = parse_args()

    clusterfile = opt.clusterfile
    if clusterfile:
        clusterRemote(opt,arg)
    else:
        clusterLocal(opt,arg)
        
            
if __name__=='__main__':
    main()
