"""An asynchronous in-process kernel"""
import threading
import time

from .ipkernel import InProcessKernel

def _execute_request(kernel, stream, ident, parent):
    super(InProcessKernel, kernel).execute_request(stream, ident, parent)
    return True


class AsyncInProcessKernel(InProcessKernel):   
    def execute_request(self, stream, ident, parent):
        # Temporary IO redirection.
        with self._redirected_io():
            self.exec_in_thread(stream, ident, parent)

            # Don not forget to add:
            # "from gevent import monkey; monkey.patch_all(thread=False)" 
            # as one of the first import statements
            #self.exec_in_coroutine(stream, ident, parent)

    def exec_in_thread(self, stream, ident, parent):
        task = threading.Thread(target=_execute_request,
                                args=(self, stream, ident, parent))
        task.start()

        while task.is_alive():
            time.sleep(0.01)

            # Assume that in-process kernels only have one frontend
            self.frontends[0].iopub_channel.process_events()

    def exec_in_coroutine(self, stream, ident, parent):
        import gevent
        task = gevent.spawn(_execute_request, self, stream, ident, parent)

        while not task.value:
            gevent.wait(timeout=0.01)
            self.frontends[0].iopub_channel.process_events()
