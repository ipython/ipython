import sys

from IPython.parallel import Client


rc = Client()
rc.block=True
view = rc[:]
view.run('communicator.py')
view.execute('com = EngineCommunicator()')

# gather the connection information into a dict
ar = view.apply_async(lambda : com.info)
peers = ar.get_dict()
# this is a dict, keyed by engine ID, of the connection info for the EngineCommunicators

# connect the engines to each other:
view.apply_sync(lambda pdict: com.connect(pdict), peers)

# now all the engines are connected, and we can communicate between them:

def broadcast(client, sender, msg_name, dest_name=None, block=None):
    """broadcast a message from one engine to all others."""
    dest_name = msg_name if dest_name is None else dest_name
    client[sender].execute('com.publish(%s)'%msg_name, block=None)
    targets = client.ids
    targets.remove(sender)
    return client[targets].execute('%s=com.consume()'%dest_name, block=None)

def send(client, sender, targets, msg_name, dest_name=None, block=None):
    """send a message from one to one-or-more engines."""
    dest_name = msg_name if dest_name is None else dest_name
    def _send(targets, m_name):
        msg = globals()[m_name]
        return com.send(targets, msg)
        
    client[sender].apply_async(_send, targets, msg_name)
    
    return client[targets].execute('%s=com.recv()'%dest_name, block=None)




