"""A script for watching all traffic on the IOPub channel (stdout/stderr/pyerr) of engines.

This connects to the default cluster, or you can pass the path to your ipcontroller-client.json

Try running this script, and then running a few jobs that print (and call sys.stdout.flush),
and you will see the print statements as they arrive, notably not waiting for the results
to finish.

You can use the zeromq SUBSCRIBE mechanism to only receive information from specific engines,
and easily filter by message type.

Authors
-------
* MinRK
"""

import os
import sys
import json
import zmq

from IPython.zmq.session import Session
from IPython.parallel.util import disambiguate_url
from IPython.utils.py3compat import str_to_bytes
from IPython.utils.path import get_security_file

def main(connection_file):
    """watch iopub channel, and print messages"""
    
    ctx = zmq.Context.instance()
    
    with open(connection_file) as f:
        cfg = json.loads(f.read())
    
    location = cfg['location']
    reg_url = cfg['url']
    session = Session(key=str_to_bytes(cfg['exec_key']))
    
    query = ctx.socket(zmq.DEALER)
    query.connect(disambiguate_url(cfg['url'], location))
    session.send(query, "connection_request")
    idents,msg = session.recv(query, mode=0)
    c = msg['content']
    iopub_url = disambiguate_url(c['iopub'], location)
    sub = ctx.socket(zmq.SUB)
    # This will subscribe to all messages:
    sub.setsockopt(zmq.SUBSCRIBE, b'')
    # replace with b'' with b'engine.1.stdout' to subscribe only to engine 1's stdout
    # 0MQ subscriptions are simple 'foo*' matches, so 'engine.1.' subscribes
    # to everything from engine 1, but there is no way to subscribe to
    # just stdout from everyone.
    # multiple calls to subscribe will add subscriptions, e.g. to subscribe to
    # engine 1's stderr and engine 2's stdout:
    # sub.setsockopt(zmq.SUBSCRIBE, b'engine.1.stderr')
    # sub.setsockopt(zmq.SUBSCRIBE, b'engine.2.stdout')
    sub.connect(iopub_url)
    while True:
        try:
            idents,msg = session.recv(sub, mode=0)
        except KeyboardInterrupt:
            return
        # ident always length 1 here
        topic = idents[0]
        if msg['msg_type'] == 'stream':
            # stdout/stderr
            # stream names are in msg['content']['name'], if you want to handle
            # them differently
            print "%s: %s" % (topic, msg['content']['data'])
        elif msg['msg_type'] == 'pyerr':
            # Python traceback
            c = msg['content']
            print topic + ':'
            for line in c['traceback']:
                # indent lines
                print '    ' + line

if __name__ == '__main__':
    if len(sys.argv) > 1:
        cf = sys.argv[1]
    else:
        # This gets the security file for the default profile:
        cf = get_security_file('ipcontroller-client.json')
    main(cf)