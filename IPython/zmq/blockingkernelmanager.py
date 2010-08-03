from kernelmanager import SubSocketChannel
from Queue import Queue, Empty


class MsgNotReady(Exception):
    pass


class BlockingSubSocketChannel(SubSocketChannel):

    def __init__(self, context, session, address=None):
        super(BlockingSubSocketChannel, self).__init__(context, session, address)
        self._in_queue = Queue()

    def call_handlers(self, msg):
        self._in_queue.put(msg)

    def msg_ready(self):
        """Is there a message that has been received?"""
        if self._in_queue.qsize() == 0:
            return False
        else:
            return True

    def get_msg(self, block=True, timeout=None):
        """Get a message if there is one that is ready."""
        try:
            msg = self.in_queue.get(block, timeout)
        except Empty:
            raise MsgNotReady('No message has been received.')
        else:
            return msg

    def get_msgs(self):
        """Get all messages that are currently ready."""
        msgs = []
        while True:
            try:
                msg = self.get_msg(block=False)
            except MsgNotReady:
                break
            else:
                msgs.append(msg)
        return msgs