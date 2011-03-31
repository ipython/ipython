#!/usr/bin/env python
"""Old ipcluster script.  Possibly to be removed."""
#-----------------------------------------------------------------------------
#  Copyright (C) 2010-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------
from __future__ import print_function

import os
import sys
import time
from subprocess import Popen, PIPE

from IPython.external.argparse import ArgumentParser, SUPPRESS

def _filter_arg(flag, args):
    filtered = []
    if flag in args:
        filtered.append(flag)
        idx = args.index(flag)
        if len(args) > idx+1:
            if not args[idx+1].startswith('-'):
                filtered.append(args[idx+1])
    return filtered

def filter_args(flags, args=sys.argv[1:]):
    filtered = []
    for flag in flags:
        if isinstance(flag, (list,tuple)):
            for f in flag:
                filtered.extend(_filter_arg(f, args))
        else:
            filtered.extend(_filter_arg(flag, args))
    return filtered

def _strip_arg(flag, args):
    while flag in args:
        idx = args.index(flag)
        args.pop(idx)
        if len(args) > idx:
            if not args[idx].startswith('-'):
                args.pop(idx)

def strip_args(flags, args=sys.argv[1:]):
    args = list(args)
    for flag in flags:
        if isinstance(flag, (list,tuple)):
            for f in flag:
                _strip_arg(f, args)
        else:
            _strip_arg(flag, args)
    return args
    

def launch_process(mod, args):
    """Launch a controller or engine in a subprocess."""
    code = "from IPython.parallel.%s import launch_new_instance;launch_new_instance()"%mod
    arguments = [ sys.executable, '-c', code ] + args
    blackholew = file(os.devnull, 'w')
    blackholer = file(os.devnull, 'r')
    
    proc = Popen(arguments, stdin=blackholer, stdout=blackholew, stderr=PIPE)
    return proc

def main():
    parser = ArgumentParser(argument_default=SUPPRESS)
    parser.add_argument('--n', '-n', type=int, default=1,
                help="The number of engines to start.")
    ns,args = parser.parse_known_args()
    n = ns.n
    
    controller = launch_process('ipcontrollerapp', args)
    for i in range(10):
        time.sleep(.1)
        if controller.poll() is not None:
            print("Controller failed to launch:")
            print (controller.stderr.read())
            sys.exit(255)
    
    print("Launched Controller")
    engines = [ launch_process('ipengineapp', args+['--ident', 'engine-%i'%i]) for i in range(n) ]
    print("%i Engines started"%n)
    
    def wait_quietly(p):
        try:
            p.wait()
        except KeyboardInterrupt:
            pass
    
    wait_quietly(controller)
    map(wait_quietly, engines)
    print ("Engines cleaned up.")

if __name__ == '__main__':
    main()