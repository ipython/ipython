from Queue import Queue, Empty
import time

from kernelmanager import KernelManager

xreq_addr = ('127.0.0.1',5575)
sub_addr = ('127.0.0.1', 5576)
rep_addr = ('127.0.0.1', 5577)


km = KernelManager(xreq_addr, sub_addr, rep_addr)
# xreq_channel = km.get_xreq_channel()
sub_channel = km.get_sub_channel()

# xreq_channel.start()
sub_channel.start()

print "Channels are started"

def printer(msg):
    print
    print msg

class CallHandler(object):

    def __init__(self):
        self.queue = Queue()

    def __call__(self, handler, msg):
        self.queue.put((handler, msg))

    def handle(self):
        try:
            handler, msg = self.queue.get(block=False)
        except Empty:
            pass
        else:
            handler(msg)

call_handler = CallHandler()
sub_channel.override_call_handler(call_handler)
sub_channel.add_handler(printer, 'pyin')
sub_channel.add_handler(printer, 'pyout')
sub_channel.add_handler(printer, 'stdout')
sub_channel.add_handler(printer, 'stderr')

for i in range(100):
    call_handler.handle()
    time.sleep(1)

# xreq_channel.join()
sub_channel.join()