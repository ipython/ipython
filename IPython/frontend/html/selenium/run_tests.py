#!/usr/bin/env python

import os
import sys
import subprocess
import shlex
import socket
import time
from threading import Thread
import functools

import nose

base = os.path.dirname(os.path.abspath(__file__))
os.chdir(base)

def log(m):
    print m

def clean_notebooks():
    for nb in [f for f in os.listdir(base) if f.endswith('.ipynb')]:
        os.remove(nb)

def verify_server_running(port, status):
    s = socket.socket()
    while status[0] != 'abort':
        try:
            s.connect(('localhost', port))
            s.close()
        except socket.error:
            time.sleep(0.2)
        else:
            status[0] = 'up'
            return

def launch(timeout=3, port=10987, flags=''):
    log('Firing up IPython notebook...')

    ipython_cmd = '''
        ipython notebook --no-browser --port=%(port)d --user="testuser"
                         --ipython-dir="." --profile="default" %(flags)s
                         ''' % {'port': port, 'flags': flags}
    p = subprocess.Popen(shlex.split(ipython_cmd))

    status = ['down']
    t = Thread(target=verify_server_running, args=(port, status))
    t.start()
    t.join(timeout)

    if status[0] != 'up':
        log('No sign of life after %d seconds. Aborting.' % timeout)
        status[0] = 'abort'
        t.join()
        sys.exit(-1)
    else:
        log('Server is alive.')

    return p

def run_nose(verbose=False):
    args = ['', '--exe', '-w', './notebook']
    if verbose:
        args.extend(['-v', '-s'])

    nose.run('notebook', argv=args)

clean_notebooks()

p = launch()
run_nose(verbose=True)
p.terminate()
