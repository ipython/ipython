import os

from IPython.core.alias import Alias
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.magic import MagicAlias
from IPython.utils.text import dedent, indent

shell = InteractiveShell.instance()
magics = shell.magics_manager.magics

def _strip_underline(line):
    chars = set(line.strip())
    if len(chars) == 1 and ('-' in chars or '=' in chars):
        return ""
    else:
        return line

def format_docstring(func):
    docstring = (func.__doc__ or "Undocumented").rstrip()
    docstring = indent(dedent(docstring))
    # Sphinx complains if indented bits have rst headings in, so strip out
    # any underlines in the docstring.
    lines = [_strip_underline(l) for l in docstring.splitlines()]
    return "\n".join(lines)

output = [
"Line magics",
"===========",
"",
]

# Case insensitive sort by name
def sortkey(s): return s[0].lower()

for name, func in sorted(magics['line'].items(), key=sortkey):
    if isinstance(func, Alias) or isinstance(func, MagicAlias):
        # Aliases are magics, but shouldn't be documented here
        # Also skip aliases to other magics
        continue
    output.extend([".. magic:: {}".format(name),
                   "",
                   format_docstring(func),
                   ""])

output.extend([
"Cell magics",
"===========",
"",
])

for name, func in sorted(magics['cell'].items(), key=sortkey):
    if name == "!":
        # Special case - don't encourage people to use %%!
        continue
    if func == magics['line'].get(name, 'QQQP'):
        # Don't redocument line magics that double as cell magics
        continue
    if isinstance(func, MagicAlias):
        continue
    output.extend([".. cellmagic:: {}".format(name),
                   "",
                   format_docstring(func),
                   ""])

here = os.path.dirname(__file__)
dest = os.path.join(here, 'source', 'interactive', 'magics-generated.txt')
with open(dest, "w") as f:
    f.write("\n".join(output))
