from IPython.core.alias import Alias
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.text import dedent, indent

shell = InteractiveShell.instance()
magic_docs = shell.magics_manager.lsmagic_docs()

def isalias(name):
    return isinstance(shell.magics_manager.magics['line'], Alias)

line_magics = magic_docs['line']
cell_magics = magic_docs['cell']

def _strip_underline(line):
    chars = set(line.strip())
    if len(chars) == 1 and ('-' in chars or '=' in chars):
        return ""
    else:
        return line

def format_docstring(docstring):
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

for name, docstring in sorted(line_magics.items(), key=sortkey):
    if isalias(name):
        # Aliases are magics, but shouldn't be documented here
        continue
    output.extend([".. magic:: {}".format(name),
                   "",
                   format_docstring(docstring),
                   ""])

output.extend([
"Cell magics",
"===========",
"",
])

for name, docstring in sorted(cell_magics.items(), key=sortkey):
    if name == "!":
        # Special case - don't encourage people to use %%!
        continue
    if docstring == line_magics.get(name, 'QQQP'):
        # Don't redocument line magics that double as cell magics
        continue
    output.extend([".. cellmagic:: {}".format(name),
                   "",
                   format_docstring(docstring),
                   ""])

with open("source/interactive/magics-generated.txt", "w") as f:
    f.write("\n".join(output))