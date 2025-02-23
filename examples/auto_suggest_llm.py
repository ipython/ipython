"""
This is an example of Fake LLM Completer for IPython, as
well as example on how to configure IPython for LLMs.

8.32 – this is provisional and may change.

To test this you can run the following command from the root of IPython
directory:

    $ ipython --TerminalInteractiveShell.llm_provider_class=examples.auto_suggest_llm.ExampleCompletionProvider

Or you can set the value in your config file, which also allows you to set a
keyboard shortcut::

    c.TerminalInteractiveShell.llm_provider_class = "examples.auto_suggest_llm.ExampleCompletionProvider"
    c.TerminalInteractiveShell.shortcuts = [
        {
            "new_keys": ["c-q"],
            "command": "IPython:auto_suggest.llm_autosuggestion",
            "new_filter": "navigable_suggestions & default_buffer_focused",
            "create": True,
        },
    ]


You can use the following configuration option to::

    c.TerminalInteractiveShell.llm_constructor_kwargs = {"model_id": "mymodel"}


For convenience and testing you can bind a  shortcut at runtime::

    In [1]: from examples.auto_suggest_llm import setup_shortcut
       ...: setup_shortcut('c-q')


Getting access to history content
---------------------------------

This uses the same providers as Jupyter AI,  In JupyterAI, providers may get
access to the current notebook content to pass as to the LLM as context.

Here Jupyter AI documents how to get such context.

https://jupyter-ai.readthedocs.io/en/latest/developers/index.html


When reusing these models you may want to pass them more context as well in
IPython to do so you can set the
`c.TerminalInteractiveShell.llm_prefix_from_history` to `"no_prefix"`,
`"input_history"` or a fully qualified name of a function that will get
imported, get passed a `HistoryManager`, and return a prefix to be added the LLM
context.


For more flexibility, subclass the provider, and access the hisotory of IPython
via:

    ```
    ip = get_ipython()
    hm = ip.history_manager()
    hm.get_range(...) # will let you select how many input/output... etc.
    ```

"""

import asyncio
import textwrap
from asyncio import FIRST_COMPLETED, Task, create_task, wait
from typing import Any, AsyncIterable, AsyncIterator, Collection, TypeVar

from jupyter_ai.completions.models import (
    InlineCompletionList,
    InlineCompletionReply,
    InlineCompletionRequest,
    InlineCompletionStreamChunk,
)
from jupyter_ai_magics import BaseProvider
from langchain_community.llms import FakeListLLM


from IPython.terminal.shortcuts import Binding
from IPython.terminal.shortcuts.filters import (
    navigable_suggestions,
    default_buffer_focused,
)
from IPython.terminal.shortcuts.auto_suggest import llm_autosuggestion


def setup_shortcut(seq):
    import IPython

    ip = IPython.get_ipython()
    ip.pt_app.key_bindings.add_binding(
        seq, filter=(navigable_suggestions & default_buffer_focused)
    )(llm_autosuggestion),


class ExampleCompletionProvider(BaseProvider, FakeListLLM):  # type: ignore[misc, valid-type]
    """
    This is an example Fake LLM provider for IPython

    As of 8.32 this is provisional and may change without any warnings
    """

    id = "my_provider"
    name = "My Provider"
    model_id_key = "model"
    models = ["model_a"]

    def __init__(self, **kwargs: Any):
        kwargs["responses"] = ["This fake response will not be used for completion"]
        kwargs["model_id"] = "model_a"
        super().__init__(**kwargs)

    async def generate_inline_completions(
        self, request: InlineCompletionRequest
    ) -> InlineCompletionReply:
        raise ValueError("IPython 8.32 only support streaming models for now.")

    async def stream_inline_completions(
        self, request: InlineCompletionRequest
    ) -> AsyncIterator[InlineCompletionStreamChunk]:
        token_1 = f"t{request.number}s0"

        yield InlineCompletionReply(
            list=InlineCompletionList(
                items=[
                    {"insertText": "It", "isIncomplete": True, "token": token_1},
                ]
            ),
            reply_to=request.number,
        )

        reply: InlineCompletionStreamChunk
        async for reply in self._stream(
            textwrap.dedent(
                """
                was then that the fox appeared.
                “Good morning,” said the fox.
                “Good morning,” the little prince responded politely, although when he turned around he saw nothing.
                “I am right here,” the voice said, “under the apple tree.”
                “Who are you?” asked the little prince, and added, “You are very pretty to look at.”
                “I am a fox,” said the fox.
                “Come and play with me,” proposed the little prince. “I am so unhappy.”
                """
            ).strip(),
            request.number,
            token_1,
            start_with="It",
        ):
            yield reply

    async def _stream(
        self, sentence: str, request_number: int, token: str, start_with: str = ""
    ) -> AsyncIterable[InlineCompletionStreamChunk]:
        suggestion = start_with

        for fragment in sentence.split(" "):
            await asyncio.sleep(0.05)
            suggestion += " " + fragment
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
