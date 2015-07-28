from __future__ import unicode_literals

from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.filters import IsDone, Always, HasFocus, RendererHeightIsKnown
from prompt_toolkit.layout import Window, HSplit, VSplit, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl, TokenListControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import HighlightSearchProcessor, HighlightSelectionProcessor, HighlightMatchingBracketProcessor, ConditionalProcessor, ShowLeadingWhiteSpaceProcessor
from prompt_toolkit.layout.screen import Char
from prompt_toolkit.layout.toolbars import ArgToolbar, SearchToolbar, SystemToolbar, TokenListToolbar

from pygments.lexers import PythonLexer
from pygments.token import Token
import IPython
import platform
import sys

__all__ = (
    'create_layout',
)


def create_layout(python_input, key_bindings_manager, lexer=PythonLexer):
    D = LayoutDimension

    def get_prompt_tokens(cli):
        ' Prompt showing something like "In [1]:". '
        return [(Token.In, python_input.prompt.lstrip())]

    def create_python_input_window():
        return Window(
            BufferControl(
                buffer_name=DEFAULT_BUFFER,
                lexer=lexer,
                input_processors=[
                                  # Show matching parentheses, but only while editing.
                                  ConditionalProcessor(
                                      processor=HighlightMatchingBracketProcessor(chars='[](){}'),
                                      filter=HasFocus(DEFAULT_BUFFER) & ~IsDone()),
                                  ShowLeadingWhiteSpaceProcessor(),
                                  HighlightSearchProcessor(preview_search=Always()),
                                  HighlightSelectionProcessor(),
                                  ],

                # Make sure that we always see the result of an reverse-i-search:
                preview_search=Always(),
            ),
            # As long as we're editing, prefer a minimal height of 6.
            get_height=(lambda cli: (None if cli.is_done else D(min=6))),
        )

    return HSplit([
        FloatContainer(
            content=HSplit([
                VSplit([
                    Window(
                        TokenListControl(get_prompt_tokens),
                        dont_extend_width=True,
                    ),
                    create_python_input_window(),
                ]),
            ]),
            floats=[
                Float(xcursor=True,
                      ycursor=True,
                      content=CompletionsMenu(
                          max_height=12))
            ]
            ),
        ArgToolbar(),
        SearchToolbar(),
        SystemToolbar(),
        StatusBar(),
    ])


class StatusBar(TokenListToolbar):
    def __init__(self, token=Token.StatusBar):
        version = sys.version_info

        def get_tokens(cli):
            return [
                    (Token.StatusBar, ' IPython '),
                    (Token.StatusBar, IPython.__version__),
                    (Token.StatusBar, ', '),
                    (Token.StatusBar, '%s %i.%i.%i' % (platform.python_implementation(),
                                                       version[0], version[1], version[2])),
            ]

        super(StatusBar, self).__init__(
            get_tokens,
            default_char=Char(token=token),
            filter=~IsDone() & RendererHeightIsKnown())
