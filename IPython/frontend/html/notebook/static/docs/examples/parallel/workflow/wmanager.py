"""Mock workflow manager.

This is a mock work manager whose submitted 'jobs' simply consist of executing
a python string.  What we want is to see the implementation of the ipython
controller part.
"""

from __future__ import print_function

import atexit
import sys

from subprocess import Popen

def cleanup(controller, engines):
    """Cleanup routine to shut down all subprocesses we opened."""
    import signal, time
    
    print('Starting cleanup')
    print('Stopping engines...')
    for e in engines:
        e.send_signal(signal.SIGINT)
    print('Stopping controller...')
    # so it can shut down its queues
    controller.send_signal(signal.SIGINT)
    time.sleep(0.1)
    print('Killing controller...')
    controller.kill()
    print('Cleanup done')


if __name__ == '__main__':

    # Start controller in separate process
    cont = Popen(['python', '-m', 'IPython.parallel.ipcontrollerapp'])
    print('Started controller')

    # "Submit jobs"
    eng = []
    for i in range(4):
        eng.append(Popen(['python', 'job_wrapper.py','x=%s' % i]))

    # Ensure that all subpro
    atexit.register(lambda : cleanup(cont, eng))
