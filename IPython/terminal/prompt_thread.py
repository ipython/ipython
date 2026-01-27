"""Background thread for running prompt_for_code concurrently with code execution."""

import asyncio
import queue
import threading
from weakref import ref


class _EOFSentinel:
    """Sentinel for EOF (Ctrl-D)."""

    pass


class _ExceptionSentinel:
    """Sentinel for exceptions in prompt thread."""

    def __init__(self, exception):
        self.exception = exception


class PromptThread(threading.Thread):
    """Runs prompt_for_code in a background thread.

    This allows users to type input while code executes on the main thread.
    Code execution stays on the main thread because some libraries don't
    support being called from non-main threads.
    """

    daemon = True

    def __init__(self, shell):
        super().__init__(name="IPythonPromptThread")
        self._shell_ref = ref(shell)
        self.input_queue = queue.Queue()
        self.stop_event = threading.Event()
        self._event_loop = None

    def run(self):
        """Main loop - continuously prompt for code."""
        # Create new event loop for this thread
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        try:
            while not self.stop_event.is_set():
                shell = self._shell_ref()
                if shell is None:
                    break

                try:
                    # Get code from prompt (blocks until user submits)
                    code = self._prompt_for_code(shell)
                    if code is not None:
                        self.input_queue.put(code)
                except EOFError:
                    self.input_queue.put(_EOFSentinel())
                except Exception as e:
                    # Don't propagate exceptions if we're stopping
                    if not self.stop_event.is_set():
                        self.input_queue.put(_ExceptionSentinel(e))
                    break
        finally:
            if self._event_loop is not None:
                self._event_loop.close()

    def _prompt_for_code(self, shell):
        """Adapted prompt_for_code for background thread.

        Runs the async prompt in this thread's event loop.
        """
        return self._event_loop.run_until_complete(
            shell._prompt_for_code_async()
        )

    def get_input(self, timeout=None):
        """Get next input from queue. Called by main thread.

        Parameters
        ----------
        timeout : float, optional
            Maximum time to wait for input in seconds.

        Returns
        -------
        str, _EOFSentinel, _ExceptionSentinel, or None
            The input code, a sentinel object, or None if timeout occurred.
        """
        try:
            return self.input_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self):
        """Signal thread to stop."""
        self.stop_event.set()
        # Interrupt the event loop if it's running
        if self._event_loop is not None:
            try:
                self._event_loop.call_soon_threadsafe(self._event_loop.stop)
            except RuntimeError:
                # Event loop may already be closed
                pass
