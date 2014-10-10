from IPython.core.alias import Alias
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.text import dedent, indent

shell = InteractiveShell.instance()
magic_docs = shell.magics_manager.lsmagic_docs()

def isalias(name):
    return isinstance(shell.magics_manager.magics['line'], Alias)

line_magics = magic_docs['line']
cell_magics = magic_docs['cell']

output = [
"Line magics",
"===========",
"",
]

for name, docstring in sorted(line_magics.items()):
    if isalias(name):
        # Aliases are magics, but shouldn't be documented here
        continue
    output.extend([".. magic:: %{}".format(name),
                   "",
                   indent(dedent(docstring)),
                   ""])

output.extend([
"Cell magics"
"==========="
"",
])

for name, docstring in sorted(cell_magics.items()):
    if docstring == line_magics.get(name, 'QQQP'):
        # Don't redocument line magics that double as cell magics
        continue
    output.extend([".. cellmagic:: %%{}".format(name),
                   "",
                   indent(dedent(docstring)),
                   ""])

with open("source/interactive/magics-generated.txt", "w") as f:
    f.write("\n".join(output))