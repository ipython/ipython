"""
Async helper function that are invalid syntax on Python 3.5 and below.

This code is best effort, and may have edge cases not behaving as expected. In
particular it contain a number of heuristics to detect whether code is
effectively async and need to run in an event loop or not.

Some constructs (like top-level `return`, or `yield`) are taken care of
explicitly to actually raise a SyntaxError and stay as close as possible to
Python semantics.
"""


import ast
import asyncio
import inspect


class _AsyncIORunner:
    def __init__(self):
        self._loop = None

    @property
    def loop(self):
        """Always returns a non-closed event loop"""
        if self._loop is None or self._loop.is_closed():
            policy = asyncio.get_event_loop_policy()
            self._loop = policy.new_event_loop()
            policy.set_event_loop(self._loop)
        return self._loop

    def __call__(self, coro):
        """
        Handler for asyncio autoawait
        """
        return self.loop.run_until_complete(coro)

    def __str__(self):
        return "asyncio"


_asyncio_runner = _AsyncIORunner()


def _curio_runner(coroutine):
    """
    handler for curio autoawait
    """
    import curio

    return curio.run(coroutine)


def _trio_runner(async_fn):
    import trio

    async def loc(coro):
        """
        We need the dummy no-op async def to protect from
        trio's internal. See https://github.com/python-trio/trio/issues/89
        """
        return await coro

    return trio.run(loc, async_fn)


def _pseudo_sync_runner(coro):
    """
    A runner that does not really allow async execution, and just advance the coroutine.

    See discussion in https://github.com/python-trio/trio/issues/608,

    Credit to Nathaniel Smith
    """
    try:
        coro.send(None)
    except StopIteration as exc:
        return exc.value
    else:
        # TODO: do not raise but return an execution result with the right info.
        raise RuntimeError(
            "{coro_name!r} needs a real async loop".format(coro_name=coro.__name__)
        )


def _should_be_async(cell: str) -> bool:
    """Detect if a block of code need to be wrapped in an `async def`

    Attempt to parse the block of code, it it compile we're fine.
    Otherwise we  wrap if and try to compile.

    If it works, assume it should be async. Otherwise Return False.

    Not handled yet: If the block of code has a return statement as the top
    level, it will be seen as async. This is a know limitation.
    """
    try:
        code = compile(
            cell, "<>", "exec", flags=getattr(ast, "PyCF_ALLOW_TOP_LEVEL_AWAIT", 0x0)
        )
        return inspect.CO_COROUTINE & code.co_flags == inspect.CO_COROUTINE
    except (SyntaxError, MemoryError):
        return False
