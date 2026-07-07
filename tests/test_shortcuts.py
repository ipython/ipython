import pytest
import sys
import time
from IPython.terminal.interactiveshell import PtkHistoryAdapter
from IPython.terminal.shortcuts.auto_suggest import (
    accept,
    accept_or_jump_to_end,
    accept_token,
    accept_character,
    accept_word,
    accept_and_keep_cursor,
    discard,
    llm_autosuggestion,
    NavigableAutoSuggestFromHistory,
    swap_autosuggestion_up,
    swap_autosuggestion_down,
)
from IPython.terminal.shortcuts.auto_match import skip_over
from IPython.terminal.shortcuts import (
    Binding,
    KEY_BINDINGS,
    add_binding,
    create_identifier,
    create_ipython_shortcuts,
    dismiss_completion,
    handle_return_or_newline_or_execute,
    indent_buffer,
    newline_autoindent,
    newline_or_execute_outer,
    next_history_or_next_completion,
    open_input_in_editor,
    previous_history_or_previous_completion,
    reformat_and_execute,
    reformat_text_before_cursor,
    reset_buffer,
    reset_search_buffer,
    suspend_to_bg,
    win_paste,
)
from IPython.terminal.shortcuts import auto_match
from IPython.terminal.shortcuts import filters
from IPython.testing import decorators as dec

from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.key_binding import KeyBindings

from unittest.mock import patch, Mock


def make_event(text, cursor, suggestion):
    event = Mock()
    event.current_buffer = Mock()
    event.current_buffer.suggestion = Mock()
    event.current_buffer.text = text
    event.current_buffer.cursor_position = cursor
    event.current_buffer.suggestion.text = suggestion
    event.current_buffer.document = Document(text=text, cursor_position=cursor)
    return event


try:
    from .fake_llm import FIBONACCI
except ImportError:
    FIBONACCI = ""


@pytest.mark.skip(reason="pydandic messed up")
@dec.skip_without("jupyter_ai")
@pytest.mark.asyncio
async def test_llm_autosuggestion():
    provider = NavigableAutoSuggestFromHistory()
    ip = get_ipython()
    ip.auto_suggest = provider
    ip.llm_provider_class = "tests.fake_llm.FibonacciCompletionProvider"
    ip.history_manager.get_range = Mock(return_value=[])
    text = "def fib"
    event = Mock()
    event.current_buffer = Buffer(
        history=PtkHistoryAdapter(ip),
    )
    event.current_buffer.insert_text(text, move_cursor=True)
    await llm_autosuggestion(event)
    assert event.current_buffer.suggestion.text == FIBONACCI[len(text) :]


def test_slow_llm_provider_should_not_block_init():
    ip = get_ipython()
    provider = NavigableAutoSuggestFromHistory()
    ip.auto_suggest = provider
    start = time.perf_counter()
    ip.llm_provider_class = "tests.fake_llm.SlowStartingCompletionProvider"
    end = time.perf_counter()
    elapsed = end - start
    assert elapsed < 0.1


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "def out(tag: str, n=50):"),
        ("def ", "out(tag: str, n=50):", "out(tag: str, n=50):"),
    ],
)
def test_accept(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    buffer = event.current_buffer
    buffer.insert_text = Mock()
    accept(event)
    assert buffer.insert_text.called
    assert buffer.insert_text.call_args[0] == (expected,)


@pytest.mark.parametrize(
    "text, suggestion",
    [
        ("", "def out(tag: str, n=50):"),
        ("def ", "out(tag: str, n=50):"),
    ],
)
def test_discard(text, suggestion):
    event = make_event(text, len(text), suggestion)
    buffer = event.current_buffer
    buffer.insert_text = Mock()
    discard(event)
    assert not buffer.insert_text.called
    assert buffer.suggestion is None


@pytest.mark.parametrize(
    "text, cursor, suggestion, called",
    [
        ("123456", 6, "123456789", True),
        ("123456", 3, "123456789", False),
        ("123456   \n789", 6, "123456789", True),
    ],
)
def test_autosuggest_at_EOL(text, cursor, suggestion, called):
    """
    test that autosuggest is only applied at end of line.
    """

    event = make_event(text, cursor, suggestion)
    event.current_buffer.insert_text = Mock()
    accept_or_jump_to_end(event)
    if called:
        event.current_buffer.insert_text.assert_called()
    else:
        event.current_buffer.insert_text.assert_not_called()
        # event.current_buffer.document.get_end_of_line_position.assert_called()


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "def "),
        ("d", "ef out(tag: str, n=50):", "ef "),
        ("de ", "f out(tag: str, n=50):", "f "),
        ("def", " out(tag: str, n=50):", " "),
        ("def ", "out(tag: str, n=50):", "out("),
        ("def o", "ut(tag: str, n=50):", "ut("),
        ("def ou", "t(tag: str, n=50):", "t("),
        ("def out", "(tag: str, n=50):", "("),
        ("def out(", "tag: str, n=50):", "tag: "),
        ("def out(t", "ag: str, n=50):", "ag: "),
        ("def out(ta", "g: str, n=50):", "g: "),
        ("def out(tag", ": str, n=50):", ": "),
        ("def out(tag:", " str, n=50):", " "),
        ("def out(tag: ", "str, n=50):", "str, "),
        ("def out(tag: s", "tr, n=50):", "tr, "),
        ("def out(tag: st", "r, n=50):", "r, "),
        ("def out(tag: str", ", n=50):", ", n"),
        ("def out(tag: str,", " n=50):", " n"),
        ("def out(tag: str, ", "n=50):", "n="),
        ("def out(tag: str, n", "=50):", "="),
        ("def out(tag: str, n=", "50):", "50)"),
        ("def out(tag: str, n=5", "0):", "0)"),
        ("def out(tag: str, n=50", "):", "):"),
        ("def out(tag: str, n=50)", ":", ":"),
    ],
)
def test_autosuggest_token(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    event.current_buffer.insert_text = Mock()
    accept_token(event)
    assert event.current_buffer.insert_text.called
    assert event.current_buffer.insert_text.call_args[0] == (expected,)


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "d"),
        ("d", "ef out(tag: str, n=50):", "e"),
        ("de ", "f out(tag: str, n=50):", "f"),
        ("def", " out(tag: str, n=50):", " "),
    ],
)
def test_accept_character(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    event.current_buffer.insert_text = Mock()
    accept_character(event)
    assert event.current_buffer.insert_text.called
    assert event.current_buffer.insert_text.call_args[0] == (expected,)


@pytest.mark.parametrize(
    "text, suggestion, expected",
    [
        ("", "def out(tag: str, n=50):", "def "),
        ("d", "ef out(tag: str, n=50):", "ef "),
        ("de", "f out(tag: str, n=50):", "f "),
        ("def", " out(tag: str, n=50):", " "),
        # (this is why we also have accept_token)
        ("def ", "out(tag: str, n=50):", "out(tag: "),
    ],
)
def test_accept_word(text, suggestion, expected):
    event = make_event(text, len(text), suggestion)
    event.current_buffer.insert_text = Mock()
    accept_word(event)
    assert event.current_buffer.insert_text.called
    assert event.current_buffer.insert_text.call_args[0] == (expected,)


@pytest.mark.parametrize(
    "text, suggestion, expected, cursor",
    [
        ("", "def out(tag: str, n=50):", "def out(tag: str, n=50):", 0),
        ("def ", "out(tag: str, n=50):", "out(tag: str, n=50):", 4),
    ],
)
def test_accept_and_keep_cursor(text, suggestion, expected, cursor):
    event = make_event(text, cursor, suggestion)
    buffer = event.current_buffer
    buffer.insert_text = Mock()
    accept_and_keep_cursor(event)
    assert buffer.insert_text.called
    assert buffer.insert_text.call_args[0] == (expected,)
    assert buffer.cursor_position == cursor


def test_autosuggest_token_empty():
    full = "def out(tag: str, n=50):"
    event = make_event(full, len(full), "")
    event.current_buffer.insert_text = Mock()

    with patch(
        "prompt_toolkit.key_binding.bindings.named_commands.forward_word"
    ) as forward_word:
        accept_token(event)
        assert not event.current_buffer.insert_text.called
        assert forward_word.called


def test_reset_search_buffer():
    event_with_text = Mock()
    event_with_text.current_buffer.document.text = "some text"
    event_with_text.current_buffer.reset = Mock()

    event_empty = Mock()
    event_empty.current_buffer.document.text = ""
    event_empty.app.layout.focus = Mock()

    reset_search_buffer(event_with_text)
    event_with_text.current_buffer.reset.assert_called_once()

    reset_search_buffer(event_empty)
    event_empty.app.layout.focus.assert_called_once_with(DEFAULT_BUFFER)


def test_other_providers():
    """Ensure that swapping autosuggestions does not break with other providers"""
    provider = AutoSuggestFromHistory()
    ip = get_ipython()
    ip.auto_suggest = provider
    event = Mock()
    event.current_buffer = Buffer()
    assert swap_autosuggestion_up(event) is None
    assert swap_autosuggestion_down(event) is None


@pytest.mark.asyncio
async def test_navigable_provider():
    provider = NavigableAutoSuggestFromHistory()
    history = InMemoryHistory(history_strings=["very_a", "very", "very_b", "very_c"])
    buffer = Buffer(history=history)
    ip = get_ipython()
    ip.auto_suggest = provider

    async for _ in history.load():
        pass

    buffer.cursor_position = 5
    buffer.text = "very"

    up = swap_autosuggestion_up
    down = swap_autosuggestion_down

    event = Mock()
    event.current_buffer = buffer

    def get_suggestion():
        suggestion = provider.get_suggestion(buffer, buffer.document)
        buffer.suggestion = suggestion
        return suggestion

    assert get_suggestion().text == "_c"

    # should go up
    up(event)
    assert get_suggestion().text == "_b"

    # should skip over 'very' which is identical to buffer content
    up(event)
    assert get_suggestion().text == "_a"

    # should cycle back to beginning
    up(event)
    assert get_suggestion().text == "_c"

    # should cycle back through end boundary
    down(event)
    assert get_suggestion().text == "_a"

    down(event)
    assert get_suggestion().text == "_b"

    down(event)
    assert get_suggestion().text == "_c"

    down(event)
    assert get_suggestion().text == "_a"


@pytest.mark.asyncio
async def test_navigable_provider_multiline_entries():
    provider = NavigableAutoSuggestFromHistory()
    history = InMemoryHistory(history_strings=["very_a\nvery_b", "very_c"])
    buffer = Buffer(history=history)
    ip = get_ipython()
    ip.auto_suggest = provider

    async for _ in history.load():
        pass

    buffer.cursor_position = 5
    buffer.text = "very"
    up = swap_autosuggestion_up
    down = swap_autosuggestion_down

    event = Mock()
    event.current_buffer = buffer

    def get_suggestion():
        suggestion = provider.get_suggestion(buffer, buffer.document)
        buffer.suggestion = suggestion
        return suggestion

    assert get_suggestion().text == "_c"

    up(event)
    assert get_suggestion().text == "_b"

    up(event)
    assert get_suggestion().text == "_a"

    down(event)
    assert get_suggestion().text == "_b"

    down(event)
    assert get_suggestion().text == "_c"


def create_session_mock():
    session = Mock()
    session.default_buffer = Buffer()
    return session


def test_navigable_provider_connection():
    provider = NavigableAutoSuggestFromHistory()
    provider.skip_lines = 1

    session_1 = create_session_mock()
    provider.connect(session_1)

    assert provider.skip_lines == 1
    session_1.default_buffer.on_text_insert.fire()
    assert provider.skip_lines == 0

    session_2 = create_session_mock()
    provider.connect(session_2)
    provider.skip_lines = 2

    assert provider.skip_lines == 2
    session_2.default_buffer.on_text_insert.fire()
    assert provider.skip_lines == 0

    provider.skip_lines = 3
    provider.disconnect()
    session_1.default_buffer.on_text_insert.fire()
    session_2.default_buffer.on_text_insert.fire()
    assert provider.skip_lines == 3


@pytest.fixture
def ipython_with_prompt():
    ip = get_ipython()
    ip.pt_app = Mock()
    ip.pt_app.key_bindings = create_ipython_shortcuts(ip)
    try:
        yield ip
    finally:
        ip.pt_app = None


def find_bindings_by_command(command):
    ip = get_ipython()
    return [
        binding
        for binding in ip.pt_app.key_bindings.bindings
        if binding.handler == command
    ]


def test_modify_unique_shortcut(ipython_with_prompt):
    original = find_bindings_by_command(accept_token)
    assert len(original) == 1

    ipython_with_prompt.shortcuts = [
        {"command": "IPython:auto_suggest.accept_token", "new_keys": ["a", "b", "c"]}
    ]
    matched = find_bindings_by_command(accept_token)
    assert len(matched) == 1
    assert list(matched[0].keys) == ["a", "b", "c"]
    assert list(matched[0].keys) != list(original[0].keys)
    assert matched[0].filter == original[0].filter

    ipython_with_prompt.shortcuts = [
        {"command": "IPython:auto_suggest.accept_token", "new_filter": "always"}
    ]
    matched = find_bindings_by_command(accept_token)
    assert len(matched) == 1
    assert list(matched[0].keys) != ["a", "b", "c"]
    assert list(matched[0].keys) == list(original[0].keys)
    assert matched[0].filter != original[0].filter


def test_disable_shortcut(ipython_with_prompt):
    matched = find_bindings_by_command(accept_token)
    assert len(matched) == 1

    ipython_with_prompt.shortcuts = [
        {"command": "IPython:auto_suggest.accept_token", "new_keys": []}
    ]
    matched = find_bindings_by_command(accept_token)
    assert len(matched) == 0

    ipython_with_prompt.shortcuts = []
    matched = find_bindings_by_command(accept_token)
    assert len(matched) == 1


def test_modify_shortcut_with_filters(ipython_with_prompt):
    matched = find_bindings_by_command(skip_over)
    matched_keys = {m.keys[0] for m in matched}
    assert matched_keys == {")", "]", "}", "'", '"'}

    with pytest.raises(ValueError, match="Multiple shortcuts matching"):
        ipython_with_prompt.shortcuts = [
            {"command": "IPython:auto_match.skip_over", "new_keys": ["x"]}
        ]

    ipython_with_prompt.shortcuts = [
        {
            "command": "IPython:auto_match.skip_over",
            "new_keys": ["x"],
            "match_filter": "focused_insert & auto_match & followed_by_single_quote",
        }
    ]
    matched = find_bindings_by_command(skip_over)
    matched_keys = {m.keys[0] for m in matched}
    assert matched_keys == {")", "]", "}", "x", '"'}


def example_command():
    pass


def test_add_shortcut_for_new_command(ipython_with_prompt):
    matched = find_bindings_by_command(example_command)
    assert len(matched) == 0

    with pytest.raises(ValueError, match="example_command is not a known"):
        ipython_with_prompt.shortcuts = [
            {"command": "example_command", "new_keys": ["x"]}
        ]
    matched = find_bindings_by_command(example_command)
    assert len(matched) == 0


def test_modify_shortcut_failure(ipython_with_prompt):
    with pytest.raises(ValueError, match="No shortcuts matching"):
        ipython_with_prompt.shortcuts = [
            {
                "command": "IPython:auto_match.skip_over",
                "match_keys": ["x"],
                "new_keys": ["y"],
            }
        ]


def test_add_shortcut_for_existing_command(ipython_with_prompt):
    matched = find_bindings_by_command(skip_over)
    assert len(matched) == 5

    with pytest.raises(ValueError, match="Cannot add a shortcut without keys"):
        ipython_with_prompt.shortcuts = [
            {"command": "IPython:auto_match.skip_over", "new_keys": [], "create": True}
        ]

    ipython_with_prompt.shortcuts = [
        {"command": "IPython:auto_match.skip_over", "new_keys": ["x"], "create": True}
    ]
    matched = find_bindings_by_command(skip_over)
    assert len(matched) == 6

    ipython_with_prompt.shortcuts = []
    matched = find_bindings_by_command(skip_over)
    assert len(matched) == 5


def test_setting_shortcuts_before_pt_app_init():
    ipython = get_ipython()
    assert ipython.pt_app is None
    shortcuts = [
        {"command": "IPython:auto_match.skip_over", "new_keys": ["x"], "create": True}
    ]
    ipython.shortcuts = shortcuts
    assert ipython.shortcuts == shortcuts


def test_navigable_provider_disconnect_removes_cursor_handler():
    provider = NavigableAutoSuggestFromHistory()
    session = create_session_mock()
    provider.connect(session)

    # Check that handlers are connected
    assert len(session.default_buffer.on_text_insert._handlers) > 0
    assert len(session.default_buffer.on_cursor_position_changed._handlers) > 0

    provider.disconnect()

    # Check that handlers are disconnected
    assert len(session.default_buffer.on_text_insert._handlers) == 0
    assert len(session.default_buffer.on_cursor_position_changed._handlers) == 0


@pytest.mark.asyncio
async def test_llm_autosuggestion_cancellation_and_error_handling():
    import sys
    import asyncio
    from unittest.mock import MagicMock, AsyncMock

    # Stub classes to mimic jupyter_ai.completions.models
    class MockInlineCompletionRequest:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class MockInlineCompletionReply:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class MockInlineCompletionStreamChunk:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    mock_jai_models = MagicMock()
    mock_jai_models.InlineCompletionRequest = MockInlineCompletionRequest
    mock_jai_models.InlineCompletionReply = MockInlineCompletionReply
    mock_jai_models.InlineCompletionStreamChunk = MockInlineCompletionStreamChunk

    mock_jai = MagicMock()
    mock_completions = MagicMock()
    mock_jai.completions = mock_completions
    mock_completions.models = mock_jai_models

    mock_magics = MagicMock()

    modules_to_patch = {
        "jupyter_ai": mock_jai,
        "jupyter_ai.completions": mock_completions,
        "jupyter_ai.completions.models": mock_jai_models,
        "jupyter_ai_magics": mock_magics,
    }

    # Use patch.dict to mock the modules during this test
    with patch.dict(sys.modules, modules_to_patch):
        provider = NavigableAutoSuggestFromHistory()
        
        # Test default prefixer is empty string
        assert provider._llm_prefixer(None) == ""

        # Setup mock provider instance
        mock_provider = MagicMock()
        provider._llm_provider_instance = mock_provider

        # Setup buffer and history
        ip = get_ipython()
        buffer = Buffer(history=PtkHistoryAdapter(ip))
        buffer.text = "test text"

        # 1. Test normal execution
        async def mock_stream_normal(request):
            yield MockInlineCompletionReply(
                list=MagicMock(items=[MagicMock(insertText="suggestion")]),
                reply_to=request.number
            )

        mock_provider.stream_inline_completions = mock_stream_normal
        await provider._trigger_llm(buffer)
        assert buffer.suggestion.text == "suggestion"

        # 2. Test cancellation
        async def mock_stream_sleep(request):
            await asyncio.sleep(5)
            yield MockInlineCompletionReply(
                list=MagicMock(items=[MagicMock(insertText="slow")]),
                reply_to=request.number
            )

        mock_provider.stream_inline_completions = mock_stream_sleep
        task = asyncio.create_task(provider._trigger_llm(buffer))
        await asyncio.sleep(0.01)
        # Cancel the task using disconnect which calls _cancel_running_llm_task
        provider.disconnect()
        # Verify it completes without raising CancelledError
        await task

        # 3. Test exception handling
        async def mock_stream_error(request):
            raise ValueError("API error")
            yield  # make it a generator

        mock_provider.stream_inline_completions = mock_stream_error
        # Verify it completes without raising the exception
        await provider._trigger_llm(buffer)


# -----------------------------------------------------------------------------
# auto_match handlers
# -----------------------------------------------------------------------------


def make_buffer_event(text="", cursor=None):
    """Create a mock event operating on a real prompt_toolkit Buffer."""
    buffer = Buffer(multiline=True)
    document = Document(text, len(text) if cursor is None else cursor)
    buffer.set_document(document, bypass_readonly=True)
    event = Mock()
    event.current_buffer = buffer
    return event


@pytest.mark.parametrize(
    "handler, expected_text",
    [
        (auto_match.parenthesis, "()"),
        (auto_match.brackets, "[]"),
        (auto_match.braces, "{}"),
        (auto_match.double_quote, '""'),
        (auto_match.single_quote, "''"),
    ],
)
def test_auto_match_pairs(handler, expected_text):
    event = make_buffer_event()
    handler(event)
    assert event.current_buffer.text == expected_text
    # cursor should end up in-between the pair
    assert event.current_buffer.cursor_position == 1


@pytest.mark.parametrize(
    "handler, text, expected_text",
    [
        (auto_match.docstring_double_quotes, '""', '""""""'),
        (auto_match.docstring_single_quotes, "''", "''''''"),
    ],
)
def test_auto_match_docstring_quotes(handler, text, expected_text):
    event = make_buffer_event(text)
    handler(event)
    assert event.current_buffer.text == expected_text
    # cursor should end up in the middle of the six quotes
    assert event.current_buffer.cursor_position == 3


@pytest.mark.parametrize(
    "handler, text, expected_text, expected_cursor",
    [
        # with dashes after the raw string prefix, dashes are mirrored
        (auto_match.raw_string_parenthesis, 'r"--', 'r"--()--', 5),
        (auto_match.raw_string_bracket, 'r"--', 'r"--[]--', 5),
        (auto_match.raw_string_braces, 'r"--', 'r"--{}--', 5),
        # uppercase prefix and single quote
        (auto_match.raw_string_parenthesis, "R'-", "R'-()-", 4),
        # no dashes: behaves like a plain pair
        (auto_match.raw_string_parenthesis, 'r"', 'r"()', 3),
        # no raw-string prefix at all: still inserts a plain pair
        (auto_match.raw_string_parenthesis, "x", "x()", 2),
    ],
)
def test_auto_match_raw_string_pairs(handler, text, expected_text, expected_cursor):
    event = make_buffer_event(text)
    handler(event)
    assert event.current_buffer.text == expected_text
    assert event.current_buffer.cursor_position == expected_cursor


def test_auto_match_skip_over():
    event = make_buffer_event("()", cursor=1)
    skip_over(event)
    assert event.current_buffer.text == "()"
    assert event.current_buffer.cursor_position == 2


@pytest.mark.parametrize("text", ["()", "[]", "{}", '""', "''"])
def test_auto_match_delete_pair(text):
    event = make_buffer_event(text, cursor=1)
    auto_match.delete_pair(event)
    assert event.current_buffer.text == ""
    assert event.current_buffer.cursor_position == 0


# -----------------------------------------------------------------------------
# filters
# -----------------------------------------------------------------------------


def app_with_document(text, cursor=None):
    app = Mock()
    app.current_buffer.document = Document(
        text, len(text) if cursor is None else cursor
    )
    return app


@pytest.mark.parametrize(
    "quote, line, expected",
    [
        ('"', "", True),
        ('"', 'a = "x"', True),
        ('"', 'a = "x', False),
        ('"', 'a = "x\\""', True),
        ("'", "it's", False),
        ("'", "'a' + 'b'", True),
    ],
)
def test_all_quotes_paired(quote, line, expected):
    assert filters.all_quotes_paired(quote, line) is expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("always", True),
        ("never", False),
        ("always & never", False),
        ("always | never", True),
        ("~never", True),
        ("~always & never", False),
    ],
)
def test_filter_from_string_logic(expression, expected):
    assert bool(filters.filter_from_string(expression)()) is expected


def test_filter_from_string_unknown_name():
    with pytest.raises(NameError, match="not a known shortcut filter"):
        filters.filter_from_string("this_is_not_a_filter")


def test_filter_from_string_unhandled_node():
    with pytest.raises(ValueError, match="Unhandled node"):
        filters.filter_from_string("1")


def test_eval_node_none():
    assert filters.eval_node(None) is None


def test_has_focus_sets_name():
    condition = filters.has_focus(DEFAULT_BUFFER)
    assert condition.func.__name__ == f"is_focused({DEFAULT_BUFFER})"


@pytest.mark.parametrize(
    "filter_name, text, cursor, expected",
    [
        ("preceded_by_opening_round_paren", "foo(", None, True),
        ("preceded_by_opening_round_paren", "foo", None, False),
        ("preceded_by_opening_bracket", "foo[", None, True),
        ("preceded_by_opening_brace", "foo{", None, True),
        ("preceded_by_double_quote", 'a = "', None, True),
        ("preceded_by_single_quote", "a = '", None, True),
        ("preceded_by_two_double_quotes", 'x = ""', None, True),
        ("preceded_by_two_double_quotes", 'x = "', None, False),
        ("preceded_by_two_single_quotes", "x = ''", None, True),
        ("preceded_by_raw_str_prefix", 'r"--', None, True),
        ("preceded_by_raw_str_prefix", 'x"--', None, False),
        # callable-pattern filters
        ("preceded_by_paired_double_quotes", 'a = "x"', None, True),
        ("preceded_by_paired_double_quotes", 'a = "x', None, False),
        ("preceded_by_paired_single_quotes", "a = 'x'", None, True),
        # following text
        ("followed_by_closing_round_paren", "()", 1, True),
        ("followed_by_closing_round_paren", "(x", 1, False),
        ("followed_by_closing_bracket", "[]", 1, True),
        ("followed_by_closing_brace", "{}", 1, True),
        ("followed_by_double_quote", '""', 1, True),
        ("followed_by_single_quote", "''", 1, True),
        ("followed_by_closing_paren_or_end", "f(x", None, True),
        ("followed_by_closing_paren_or_end", "f(x)", 3, True),
        ("followed_by_closing_paren_or_end", "f(xy", 3, False),
    ],
)
def test_preceding_following_text_filters(filter_name, text, cursor, expected):
    app = app_with_document(text, cursor)
    with patch.object(filters, "get_app", return_value=app):
        assert bool(filters.KEYBINDING_FILTERS[filter_name]()) is expected


@pytest.mark.parametrize(
    "text, cursor, expected",
    [
        ("print(", None, True),
        ('print("a', None, False),
        ('a = "x" + ', None, True),
        ("'''triple quoted''' ", None, True),
        ('x = "escaped \\" quote', None, False),
    ],
)
def test_not_inside_unclosed_string(text, cursor, expected):
    app = app_with_document(text, cursor)
    with patch.object(filters, "get_app", return_value=app):
        assert bool(filters.not_inside_unclosed_string()) is expected


@pytest.mark.parametrize(
    "text, cursor, expected",
    [
        ("", None, True),
        ("    ", None, True),
        ("  x", None, False),
    ],
)
def test_cursor_in_leading_ws(text, cursor, expected):
    app = app_with_document(text, cursor)
    with patch.object(filters, "get_app", return_value=app):
        assert bool(filters.cursor_in_leading_ws()) is expected


def test_line_position_filters():
    with patch.object(filters, "get_app", return_value=app_with_document("a\nb\nc", 0)):
        assert bool(filters.has_line_below()) is True
        assert bool(filters.has_line_above()) is False
        assert bool(filters.is_cursor_at_the_end_of_line()) is False

    with patch.object(filters, "get_app", return_value=app_with_document("a\nb\nc", 5)):
        assert bool(filters.has_line_below()) is False
        assert bool(filters.has_line_above()) is True
        assert bool(filters.is_cursor_at_the_end_of_line()) is True


def test_preceding_following_text_cache():
    assert filters.preceding_text(r".*\($") is filters.preceding_text(r".*\($")
    assert filters.following_text(r"^\)") is filters.following_text(r"^\)")


def test_shell_dependent_filters(monkeypatch):
    ip = get_ipython()

    monkeypatch.setattr(ip, "auto_match", True)
    assert bool(filters.auto_match()) is True
    monkeypatch.setattr(ip, "auto_match", False)
    assert bool(filters.auto_match()) is False

    monkeypatch.setattr(ip, "emacs_bindings_in_vi_insert_mode", True)
    assert bool(filters.ebivim()) is True
    monkeypatch.setattr(ip, "emacs_bindings_in_vi_insert_mode", False)
    assert bool(filters.ebivim()) is False

    monkeypatch.setattr(ip, "auto_suggest", NavigableAutoSuggestFromHistory())
    assert bool(filters.navigable_suggestions()) is True
    monkeypatch.setattr(ip, "auto_suggest", AutoSuggestFromHistory())
    assert bool(filters.navigable_suggestions()) is False

    monkeypatch.setattr(ip, "display_completions", "readlinelike")
    assert bool(filters.readline_like_completions()) is True
    monkeypatch.setattr(ip, "display_completions", "multicolumn")
    assert bool(filters.readline_like_completions()) is False

    import signal

    assert bool(filters.supports_suspend()) is hasattr(signal, "SIGTSTP")
    assert bool(filters.is_windows_os()) is (sys.platform == "win32")


def test_pass_through_filter():
    pt = filters.PassThrough()
    assert bool(pt()) is True

    observed = []
    event = Mock()
    event.key_processor.process_keys = Mock(side_effect=lambda: observed.append(pt()))
    pt.reply(event)

    event.key_processor.reset.assert_called_once()
    event.key_processor.feed_multiple.assert_called_once_with(event.key_sequence)
    event.key_processor.process_keys.assert_called_once()
    # while replying, the filter must be False so that the binding
    # does not catch the re-fed keys again
    assert observed == [False]
    # and it must reset to True afterwards
    assert bool(pt()) is True


# -----------------------------------------------------------------------------
# shortcuts (IPython.terminal.shortcuts.__init__)
# -----------------------------------------------------------------------------


def test_create_identifier():
    assert (
        create_identifier(auto_match.parenthesis) == "IPython:auto_match.parenthesis"
    )

    def some_handler(event):
        pass

    some_handler.__module__ = "singlemodule"
    assert create_identifier(some_handler) == "singlemodule:some_handler"


def test_binding_post_init():
    with_condition = Binding(skip_over, ["x"], "always")
    assert with_condition.filter is not None
    assert bool(with_condition.filter()) is True

    without_condition = Binding(skip_over, ["x"])
    assert without_condition.filter is None


def test_add_binding():
    kb = KeyBindings()
    add_binding(kb, Binding(skip_over, ["x"], "always"))
    add_binding(kb, Binding(indent_buffer, ["y"]))
    assert len(kb.bindings) == 2
    assert kb.bindings[0].handler == skip_over
    assert kb.bindings[1].handler == indent_buffer


def test_create_ipython_shortcuts_skip():
    ip = get_ipython()
    kb = create_ipython_shortcuts(ip)
    kb_skipped = create_ipython_shortcuts(ip, skip=[KEY_BINDINGS[0]])
    assert len(kb.bindings) == len(KEY_BINDINGS)
    assert len(kb_skipped.bindings) == len(KEY_BINDINGS) - 1


def test_newline_or_execute_incomplete_input():
    # incomplete input inserts a newline with auto-indentation
    event = make_buffer_event("def f():")
    handle_return_or_newline_or_execute(event)
    assert event.current_buffer.text == "def f():\n    "


def test_newline_or_execute_complete_input():
    accepted = []
    buffer = Buffer(
        accept_handler=lambda buff: accepted.append(buff.text) or False,
        multiline=True,
    )
    buffer.insert_text("a = 1")
    event = Mock()
    event.current_buffer = buffer
    handle_return_or_newline_or_execute(event)
    assert accepted == ["a = 1"]


def test_newline_or_execute_in_middle_of_multiline():
    # cursor on a line above the last one: insert a newline, do not execute
    accepted = []
    buffer = Buffer(
        accept_handler=lambda buff: accepted.append(buff.text) or False,
        multiline=True,
    )
    buffer.set_document(Document("a = 1\nb = 2", 5), bypass_readonly=True)
    event = Mock()
    event.current_buffer = buffer
    handle_return_or_newline_or_execute(event)
    assert accepted == []
    assert buffer.text == "a = 1\n\nb = 2"


def test_newline_or_execute_without_autoindent(monkeypatch):
    ip = get_ipython()
    monkeypatch.setattr(ip, "autoindent", False)

    # incomplete input: plain newline, no indentation
    event = make_buffer_event("def f():")
    handle_return_or_newline_or_execute(event)
    assert event.current_buffer.text == "def f():\n"

    # middle of a multi-line buffer: plain newline as well
    event = make_buffer_event("a = 1\nb = 2", cursor=5)
    handle_return_or_newline_or_execute(event)
    assert event.current_buffer.text == "a = 1\n\nb = 2"


def test_newline_or_execute_with_text_after_cursor():
    # complete single-line input executes even with the cursor at the start
    accepted = []
    buffer = Buffer(
        accept_handler=lambda buff: accepted.append(buff.text) or False,
        multiline=True,
    )
    buffer.set_document(Document("a = 1", 0), bypass_readonly=True)
    event = Mock()
    event.current_buffer = buffer
    handle_return_or_newline_or_execute(event)
    assert accepted == ["a = 1"]


def test_handle_return_uses_shell_handle_return(monkeypatch):
    ip = get_ipython()
    inner = Mock()
    handle_return = Mock(return_value=inner)
    monkeypatch.setattr(ip, "handle_return", handle_return, raising=False)
    event = Mock()
    handle_return_or_newline_or_execute(event)
    handle_return.assert_called_once_with(ip)
    inner.assert_called_once_with(event)


def test_newline_or_execute_with_completion_state():
    ip = get_ipython()

    event = Mock()
    event.current_buffer.complete_state.current_completion = "completion"
    newline_or_execute_outer(ip)(event)
    event.current_buffer.apply_completion.assert_called_once_with("completion")

    event = Mock()
    event.current_buffer.complete_state.current_completion = None
    newline_or_execute_outer(ip)(event)
    event.current_buffer.cancel_completion.assert_called_once()


def test_reformat_and_execute():
    accepted = []
    buffer = Buffer(
        accept_handler=lambda buff: accepted.append(buff.text) or False,
        multiline=True,
    )
    buffer.insert_text("a = 1")
    event = Mock()
    event.current_buffer = buffer
    reformat_and_execute(event)
    assert accepted == ["a = 1"]


def test_reformat_text_before_cursor_error_restores_text():
    buffer = Buffer(multiline=True)
    buffer.insert_text("a = 1")
    shell = Mock()
    shell.reformat_handler = Mock(side_effect=ValueError("reformat failed"))
    reformat_text_before_cursor(buffer, buffer.document, shell)
    assert buffer.text == "a = 1"


def test_previous_and_next_history_or_completion():
    event = Mock()
    previous_history_or_previous_completion(event)
    event.current_buffer.auto_up.assert_called_once()

    event = Mock()
    next_history_or_next_completion(event)
    event.current_buffer.auto_down.assert_called_once()


def test_dismiss_completion():
    event = Mock()
    event.current_buffer.complete_state = True
    dismiss_completion(event)
    event.current_buffer.cancel_completion.assert_called_once()

    event = Mock()
    event.current_buffer.complete_state = None
    dismiss_completion(event)
    event.current_buffer.cancel_completion.assert_not_called()


def test_reset_buffer():
    event = Mock()
    event.current_buffer.complete_state = True
    reset_buffer(event)
    event.current_buffer.cancel_completion.assert_called_once()
    event.current_buffer.reset.assert_not_called()

    event = Mock()
    event.current_buffer.complete_state = None
    reset_buffer(event)
    event.current_buffer.reset.assert_called_once()


def test_indent_buffer():
    event = make_buffer_event()
    indent_buffer(event)
    assert event.current_buffer.text == " " * 4


def test_newline_autoindent():
    event = make_buffer_event("def f():")
    newline_autoindent(event)
    assert event.current_buffer.text == "def f():\n    "
    # cursor does not move
    assert event.current_buffer.cursor_position == len("def f():")


def test_newline_autoindent_cancels_completion():
    event = Mock()
    event.current_buffer.document = Document("a = 1", 5)
    event.current_buffer.complete_state = True
    newline_autoindent(event)
    event.current_buffer.cancel_completion.assert_called_once()
    event.current_buffer.insert_text.assert_called_once_with(
        "\n", move_cursor=False
    )


def test_suspend_to_bg():
    event = Mock()
    suspend_to_bg(event)
    event.app.suspend_to_background.assert_called_once()


def test_open_input_in_editor():
    event = Mock()
    open_input_in_editor(event)
    event.app.current_buffer.open_in_editor.assert_called_once()


@pytest.mark.skipif(sys.platform == "win32", reason="tests the non-Windows stub")
def test_win_paste_stub():
    event = Mock()
    assert win_paste(event) is None
    event.current_buffer.insert_text.assert_not_called()


def test_vi_mode_with_modal_cursor(monkeypatch):
    from prompt_toolkit.key_binding.vi_state import InputMode, ViState

    ip = get_ipython()
    monkeypatch.setattr(ip, "editing_mode", "vi")
    monkeypatch.setattr(ip, "modal_cursor", True)

    original_property = ViState.input_mode
    assert "_input_mode" not in ViState.__dict__
    try:
        create_ipython_shortcuts(ip)
        assert isinstance(ViState.__dict__["input_mode"], property)
        vi_state = ViState()
        vi_state.input_mode = InputMode.NAVIGATION
        assert vi_state._input_mode == InputMode.NAVIGATION
        assert vi_state.input_mode == InputMode.NAVIGATION
    finally:
        ViState.input_mode = original_property
        if "_input_mode" in ViState.__dict__:
            del ViState._input_mode
