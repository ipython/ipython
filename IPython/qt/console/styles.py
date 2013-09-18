""" Style utilities, templates, and defaults for syntax highlighting widgets.
"""
#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from colorsys import rgb_to_hls
from pygments.styles import get_style_by_name
from pygments.token import Token

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# The default light style sheet: black text on a white background.
default_light_style_template = '''
    QPlainTextEdit, QTextEdit { background-color: %(bgcolor)s;
            color: %(fgcolor)s ;
            selection-background-color: %(select)s}
    .error { color: red; }
    .in-prompt { color: navy; }
    .in-prompt-number { font-weight: bold; }
    .out-prompt { color: darkred; }
    .out-prompt-number { font-weight: bold; }
    .inverted { background-color: %(fgcolor)s ; color:%(bgcolor)s;}
'''
default_light_style_sheet = default_light_style_template%dict(
                bgcolor='white', fgcolor='black', select="#ccc")
default_light_syntax_style = 'default'

# The default dark style sheet: white text on a black background.
default_dark_style_template = '''
    QPlainTextEdit, QTextEdit { background-color: %(bgcolor)s;
            color: %(fgcolor)s ;
            selection-background-color: %(select)s}
    QFrame { border: 1px solid grey; }
    .error { color: red; }
    .in-prompt { color: lime; }
    .in-prompt-number { color: lime; font-weight: bold; }
    .out-prompt { color: red; }
    .out-prompt-number { color: red; font-weight: bold; }
    .inverted { background-color: %(fgcolor)s ; color:%(bgcolor)s;}
'''
default_dark_style_sheet = default_dark_style_template%dict(
                bgcolor='black', fgcolor='white', select="#555")
default_dark_syntax_style = 'monokai'

# The default monochrome
default_bw_style_sheet = '''
    QPlainTextEdit, QTextEdit { background-color: white;
            color: black ;
            selection-background-color: #cccccc}
    .in-prompt-number { font-weight: bold; }
    .out-prompt-number { font-weight: bold; }
    .inverted { background-color: black ; color: white;}
'''
default_bw_syntax_style = 'bw'


def hex_to_rgb(color):
    """Convert a hex color to rgb integer tuple."""
    if color.startswith('#'):
        color = color[1:]
    if len(color) == 3:
        color = ''.join([c*2 for c in color])
    if len(color) != 6:
        return False
    try:
        r = int(color[:2],16)
        g = int(color[2:4],16)
        b = int(color[4:],16)
    except ValueError:
        return False
    else:
        return r,g,b

def dark_color(color):
    """Check whether a color is 'dark'.

    Currently, this is simply whether the luminance is <50%"""
    rgb = hex_to_rgb(color)
    if rgb:
        return rgb_to_hls(*rgb)[1] < 128
    else: # default to False
        return False

def dark_style(stylename):
    """Guess whether the background of the style with name 'stylename'
    counts as 'dark'."""
    return dark_color(get_style_by_name(stylename).background_color)

def get_colors(stylename):
    """Construct the keys to be used building the base stylesheet
    from a templatee."""
    style = get_style_by_name(stylename)
    fgcolor = style.style_for_token(Token.Text)['color'] or ''
    if len(fgcolor) in (3,6):
        # could be 'abcdef' or 'ace' hex, which needs '#' prefix
        try:
            int(fgcolor, 16)
        except TypeError:
            pass
        else:
            fgcolor = "#"+fgcolor

    return dict(
        bgcolor = style.background_color,
        select = style.highlight_color,
        fgcolor = fgcolor
    )

def sheet_from_template(name, colors='lightbg'):
    """Use one of the base templates, and set bg/fg/select colors."""
    colors = colors.lower()
    if colors=='lightbg':
        return default_light_style_template%get_colors(name)
    elif colors=='linux':
        return default_dark_style_template%get_colors(name)
    elif colors=='nocolor':
        return default_bw_style_sheet
    else:
        raise KeyError("No such color scheme: %s"%colors)
