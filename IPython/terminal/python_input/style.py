from __future__ import unicode_literals

from pygments.token import Token, Keyword, Name, Comment, String, Operator, Number
from pygments.style import Style
from pygments.styles.default import DefaultStyle
from prompt_toolkit.styles import default_style_extensions

import sys

__all__ = (
    'get_style',
)


def get_style():
    """
    Generate Pygments Style class.
    """
    class PythonStyle(Style):
        styles = {}
        styles.update(default_style_extensions)
        styles.update(ui_style)

        if sys.platform == 'win32':
            styles.update(win32_code_style)
        else:
            styles.update(DefaultStyle.styles)

    return PythonStyle


# Code style for Windows consoles. They support only 16 colors,
# so we choose a combination that displays nicely.
win32_code_style = {
    Comment:                   "#00ff00",
    Keyword:                   '#44ff44',
    Number:                    '',
    Operator:                  '',
    String:                    '#ff44ff',

    Name:                      '',
    Name.Decorator:            '#ff4444',
    Name.Class:                '#ff4444',
    Name.Function:             '#ff4444',
    Name.Builtin:              '#ff4444',

    Name.Attribute:            '',
    Name.Constant:             '',
    Name.Entity:               '',
    Name.Exception:            '',
    Name.Label:                '',
    Name.Namespace:            '',
    Name.Tag:                  '',
    Name.Variable:             '',
}


ui_style = {
    # (Python) Prompt: "In [1]:"
    Token.In:                                     'bold #008800',
    Token.In.Number:                              '',

#    # Return value.
#    Token.Out:                                    '#ff0000',
#    Token.Out.Number:                             '#ff0000',

    # Search toolbar.
    Token.Toolbar.Search:                         '#22aaaa noinherit',
    Token.Toolbar.Search.Text:                    'noinherit',

    # System toolbar
    Token.Toolbar.System.Prefix:                  '#22aaaa noinherit',

    # "arg" toolbar.
    Token.Toolbar.Arg:                            '#22aaaa noinherit',
    Token.Toolbar.Arg.Text:                       'noinherit',

    # When Control-C has been pressed. Grayed.
    Token.Aborted:                                '#888888',

    Token.LeadingWhiteSpace:                      '#888888',
    Token.StatusBar:                              'bg:#222222 #aaaaaa',
}
