import asyncio
from time import sleep

try:
    from jupyter_ai_magics.providers import BaseProvider
    from langchain_community.llms import FakeListLLM
except ImportError:

    class BaseProvider:
        pass

    class FakeListLLM:
        pass


FIBONACCI = """\
def fib(n):
    if n < 2: return n
    return fib(n - 1) + fib(n - 2)
"""


class FibonacciCompletionProvider(BaseProvider, FakeListLLM):  # type: ignore[misc, valid-type]
    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = ["model_a"]

    def __init__(self, **kwargs):
        kwargs["responses"] = ["This fake response will not be used for completion"]
        kwargs["model_id"] = "model_a"
        super().__init__(**kwargs)

    async def generate_inline_completions(self, request):
        raise ValueError("IPython only supports streaming models.")

    async def stream_inline_completions(self, request):
        from jupyter_ai.completions.models import (
            InlineCompletionList,
            InlineCompletionReply,
        )

        assert request.number > 0
        token = f"t{request.number}s0"
        last_line = request.prefix.splitlines()[-1]

        if not FIBONACCI.startswith(last_line):
            return

        yield InlineCompletionReply(
            list=InlineCompletionList(
                items=[
                    {"insertText": "", "isIncomplete": True, "token": token},
                ]
            ),
            reply_to=request.number,
        )

        async for reply in self._stream(
            FIBONACCI[len(last_line) :],
            request.number,
            token,
        ):
            yield reply

    async def _stream(self, sentence, request_number, token, start_with=""):
        from jupyter_ai.completions.models import InlineCompletionStreamChunk

        suggestion = start_with

        for fragment in sentence.split(" "):
            await asyncio.sleep(0.05)
            if suggestion:
                suggestion += " "
            suggestion += fragment
            yield InlineCompletionStreamChunk(
                type="stream",
                response={"insertText": suggestion, "token": token},
                reply_to=request_number,
                done=False,
            )

        # finally, send a message confirming that we are done
        yield InlineCompletionStreamChunk(
            type="stream",
            response={"insertText": suggestion, "token": token},
            reply_to=request_number,
            done=True,
        )


class SlowStartingCompletionProvider(BaseProvider, FakeListLLM):  # type: ignore[misc, valid-type]
    id = "slow_provider"
    name = "Slow Provider"
    model_id_key = "model"
    models = ["model_a"]

    def __init__(self, **kwargs):
        kwargs["responses"] = ["This fake response will be used for completion"]
        kwargs["model_id"] = "model_a"
        sleep(10)
        super().__init__(**kwargs)
