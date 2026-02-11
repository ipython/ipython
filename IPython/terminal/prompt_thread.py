"""Background thread for running prompt_for_code concurrently with code execution."""

import asyncio
import builtins
import queue
import sys
import threading
from typing import Any, Iterator, Literal, Optional, Union
from weakref import ref, ReferenceType

# Store the original input function
_original_input = builtins.input


class _EOFSentinel:
    """Sentinel for EOF (Ctrl-D).

    Parameters
    ----------
    should_exit : bool
        Whether the user confirmed they want to exit.
    """

    def __init__(self, should_exit: bool = True) -> None:
        self.should_exit = should_exit


class _ExceptionSentinel:
    """Sentinel for exceptions in prompt thread."""

    def __init__(self, exception: BaseException) -> None:
        self.exception = exception


class _InputRequest:
    """Request for input from the main thread."""

    def __init__(self, prompt: str, password: bool = False) -> None:
        self.prompt = prompt
        self.password = password


class _InputResponse:
    """Response to an input request."""

    def __init__(self, value: Optional[str] = None, exception: Optional[BaseException] = None) -> None:
        self.value = value
        self.exception = exception


class PromptThread(threading.Thread):
    """Runs prompt_for_code in a background thread.

    This allows users to type input while code executes on the main thread.
    Code execution stays on the main thread because some libraries don't
    support being called from non-main threads.
    """

    daemon = True

    def __init__(self, shell: Any) -> None:
        super().__init__(name="IPythonPromptThread")
        self._shell_ref: ReferenceType[Any] = ref(shell)
        self.input_queue: queue.Queue[Union[str, _EOFSentinel, _ExceptionSentinel]] = queue.Queue()  # Code/sentinels -> main thread
        self.request_queue: queue.Queue[_InputRequest] = queue.Queue()  # Input requests from main thread
        self.response_queue: queue.Queue[_InputResponse] = queue.Queue()  # Responses to main thread
        self.stop_event = threading.Event()
        self._pause_event = threading.Event()  # Set when prompting should pause
        self._paused_event = threading.Event()  # Set when prompt is actually paused
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None
        self._prompt_session: Any = None  # For simple prompts (yes/no, input requests)

    def run(self) -> None:
        """Main loop - continuously prompt for code."""
        from prompt_toolkit import PromptSession
        from prompt_toolkit.patch_stdout import patch_stdout

        # Create new event loop for this thread
        self._event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._event_loop)

        # Create a simple prompt session for yes/no questions and input requests
        self._prompt_session = PromptSession()

        try:
            while not self.stop_event.is_set():
                # Check if we should pause
                if self._pause_event.is_set():
                    self._paused_event.set()
                    # Wait until unpaused or stopped
                    while self._pause_event.is_set() and not self.stop_event.is_set():
                        # Check for input requests while paused
                        try:
                            request = self.request_queue.get(timeout=0.1)
                            self._handle_input_request(request)
                        except queue.Empty:
                            pass
                    self._paused_event.clear()
                    continue

                # Check for pending input requests
                try:
                    request = self.request_queue.get_nowait()
                    self._handle_input_request(request)
                    continue
                except queue.Empty:
                    pass

                shell = self._shell_ref()
                if shell is None:
                    break

                try:
                    # Get code from prompt (blocks until user submits)
                    code = self._prompt_for_code(shell)
                    if code is not None:
                        self.input_queue.put(code)
                except EOFError:
                    # Handle exit confirmation in the prompt thread
                    should_exit = self._handle_eof(shell)
                    if should_exit:
                        self.input_queue.put(_EOFSentinel(should_exit=True))
                        break
                    # User said no, continue prompting
                except Exception as e:
                    # Don't propagate exceptions if we're stopping
                    if not self.stop_event.is_set():
                        self.input_queue.put(_ExceptionSentinel(e))
                    break
        finally:
            if self._event_loop is not None:
                self._event_loop.close()

    def _prompt_for_code(self, shell: Any) -> Optional[str]:
        """Adapted prompt_for_code for background thread.

        Runs the async prompt in this thread's event loop.
        Uses a monitoring task to handle input requests during prompting.
        """
        assert self._event_loop is not None
        return self._event_loop.run_until_complete(
            self._prompt_with_request_monitoring(shell)
        )

    async def _prompt_with_request_monitoring(self, shell: Any) -> Optional[str]:
        """Run the prompt while monitoring for input requests.

        If an input request comes in while the user is typing, we need to
        handle it. This uses a background task to check the request queue.
        """
        prompt_task = asyncio.create_task(shell._prompt_for_code_async())
        monitor_task = asyncio.create_task(self._monitor_requests())

        try:
            # Wait for either the prompt to complete or a request to come in
            done, pending = await asyncio.wait(
                [prompt_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            if prompt_task in done:
                # User submitted code, cancel the monitor
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
                return prompt_task.result()
            else:
                # Request came in, cancel the prompt (user loses partial input)
                prompt_task.cancel()
                try:
                    await prompt_task
                except asyncio.CancelledError:
                    pass
                # Handle the request
                request = monitor_task.result()
                if request is not None:
                    self._handle_input_request(request)
                # Return None to indicate no code was submitted
                # The main loop will continue and prompt again
                return None
        except asyncio.CancelledError:
            prompt_task.cancel()
            monitor_task.cancel()
            raise

    async def _monitor_requests(self) -> Optional[_InputRequest]:
        """Monitor the request queue for input requests.

        Returns the request when one is found.
        """
        while True:
            try:
                request = self.request_queue.get_nowait()
                return request
            except queue.Empty:
                # Check periodically
                await asyncio.sleep(0.1)

    def _handle_eof(self, shell: Any) -> bool:
        """Handle EOF (Ctrl-D). Returns True if should exit.

        This runs in the prompt thread so we can use prompt_toolkit
        for the confirmation dialog without stdin conflicts.
        """
        from prompt_toolkit.patch_stdout import patch_stdout

        if not shell.confirm_exit:
            return True

        try:
            with patch_stdout(raw=True):
                assert self._event_loop is not None
                assert self._prompt_session is not None
                answer = self._event_loop.run_until_complete(
                    self._prompt_session.prompt_async(
                        "Do you really want to exit ([y]/n)? "
                    )
                )
                answer = answer.strip().lower()
                return answer in ("", "y", "yes")
        except EOFError:
            # Another Ctrl-D means yes, exit
            return True
        except Exception:
            # On any error, don't exit
            return False

    def _handle_input_request(self, request: _InputRequest) -> None:
        """Handle an input request from the main thread."""
        from prompt_toolkit.patch_stdout import patch_stdout

        try:
            with patch_stdout(raw=True):
                assert self._event_loop is not None
                assert self._prompt_session is not None
                if request.password:
                    value = self._event_loop.run_until_complete(
                        self._prompt_session.prompt_async(
                            request.prompt, is_password=True
                        )
                    )
                else:
                    value = self._event_loop.run_until_complete(
                        self._prompt_session.prompt_async(request.prompt)
                    )
                self.response_queue.put(_InputResponse(value=value))
        except EOFError as e:
            self.response_queue.put(_InputResponse(exception=e))
        except KeyboardInterrupt as e:
            self.response_queue.put(_InputResponse(exception=e))
        except Exception as e:
            self.response_queue.put(_InputResponse(exception=e))

    def get_input(self, timeout: Optional[float] = None) -> Union[str, _EOFSentinel, _ExceptionSentinel, None]:
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

    def flush_input_queue(self) -> int:
        """Discard all pending inputs in the queue.

        Called when user interrupts execution to cancel queued commands.
        Returns the number of items flushed.
        """
        count = 0
        while True:
            try:
                self.input_queue.get_nowait()
                count += 1
            except queue.Empty:
                break
        return count

    def request_input(self, prompt: str, password: bool = False, timeout: Optional[float] = None) -> str:
        """Request input from the prompt thread. Called by main thread.

        This allows the main thread to get user input without conflicting
        with the prompt thread's ownership of stdin.

        Parameters
        ----------
        prompt : str
            The prompt to display.
        password : bool, optional
            Whether to hide input (for passwords).
        timeout : float, optional
            Maximum time to wait for response.

        Returns
        -------
        str
            The user's input.

        Raises
        ------
        EOFError
            If the user pressed Ctrl-D.
        KeyboardInterrupt
            If the user pressed Ctrl-C.
        TimeoutError
            If timeout was reached.
        """
        self.request_queue.put(_InputRequest(prompt, password))
        try:
            response = self.response_queue.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError("Timed out waiting for input")

        if response.exception is not None:
            raise response.exception
        assert response.value is not None
        return response.value

    def pause(self) -> None:
        """Pause prompting. Called when something else needs stdin."""
        self._pause_event.set()
        # Wait for the prompt to actually pause (with timeout)
        self._paused_event.wait(timeout=5.0)

    def resume(self) -> None:
        """Resume prompting."""
        self._pause_event.clear()

    def stop(self) -> None:
        """Signal thread to stop."""
        self.stop_event.set()
        self._pause_event.clear()  # Unpause if paused
        # Interrupt the event loop if it's running
        if self._event_loop is not None:
            try:
                self._event_loop.call_soon_threadsafe(self._event_loop.stop)
            except RuntimeError:
                # Event loop may already be closed
                pass


class StdinWrapper:
    """Wrapper around stdin that pauses the prompt thread when read.

    This prevents stdin conflicts when user code calls input() while
    the prompt thread is active.
    """

    def __init__(self, original_stdin: Any, prompt_thread: PromptThread) -> None:
        self._original = original_stdin
        self._prompt_thread = prompt_thread

    def read(self, *args: Any, **kwargs: Any) -> Any:
        self._prompt_thread.pause()
        try:
            return self._original.read(*args, **kwargs)
        finally:
            self._prompt_thread.resume()

    def readline(self, *args: Any, **kwargs: Any) -> Any:
        self._prompt_thread.pause()
        try:
            return self._original.readline(*args, **kwargs)
        finally:
            self._prompt_thread.resume()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._original, name)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._original)

    def __next__(self) -> Any:
        self._prompt_thread.pause()
        try:
            return next(self._original)
        finally:
            self._prompt_thread.resume()


class InputPatcher:
    """Context manager that patches builtins.input to use the prompt thread.

    This ensures that calls to input() from user code are routed through
    the prompt thread, avoiding stdin conflicts.
    """

    def __init__(self, prompt_thread: PromptThread) -> None:
        self._prompt_thread = prompt_thread
        self._original_input: Optional[Any] = None

    def __enter__(self) -> "InputPatcher":
        self._original_input = builtins.input

        prompt_thread = self._prompt_thread

        def patched_input(prompt: object = "") -> str:
            """Patched input() that routes through the prompt thread."""
            return prompt_thread.request_input(str(prompt))

        builtins.input = patched_input  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
        builtins.input = self._original_input  # type: ignore[assignment]
        return False
