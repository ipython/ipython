"""
A Distributed Hello world
Ken Kinder <ken@kenkinder.com>
"""
from IPython.parallel import Client

rc = Client()

def sleep_and_echo(t, msg):
    import time
    time.sleep(t)
    return msg
    
view = rc.load_balanced_view()

world = view.apply_async(sleep_and_echo, 3, 'World!')
hello = view.apply_async(sleep_and_echo, 2, 'Hello')
print "Submitted tasks:", hello.msg_ids, world.msg_ids
print hello.get(), world.get()
