from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)
from IPython.core.display import display_png
from IPython.extensions.graphvizmagic import run_dot

from sphinx.ext.inheritance_diagram import InheritanceGraph


@magics_class
class HierarchyMagic(Magics):

    @magic_arguments()
    @argument(
        '-r', '--rankdir', default='TB',
        help='direction of the hierarchy graph (default: %(default)s)'
    )
    @argument(
        '-s', '--size', default='5.0, 12.0',
        help='size of the generated figure (default: %(default)s)',
    )
    @argument(
        'object',
        help='Class hierarchy of this class or object will be drawn',
    )
    @line_magic
    def hierarchy(self, parameter_s=''):
        """Draw hierarchy of a given class."""
        args = parse_argstring(self.hierarchy, parameter_s)
        obj = self.shell.ev(args.object)
        if isinstance(obj, type):
            objclass = obj
        elif hasattr(obj, "__class__"):
            objclass = obj.__class__
        else:
            raise ValueError(
                "Given object {0} is not a class or an instance".format(obj))
        classpath = self.shell.display_formatter.format(
            objclass, ['text/plain'])['text/plain']
        (dirpath, basepath) = classpath.rsplit('.', 1)
        ig = InheritanceGraph([basepath], dirpath)
        code = ig.generate_dot('inheritance_graph',
                               graph_attrs={'rankdir': args.rankdir,
                                            'size': '"{0}"'.format(args.size)})
        stdout = run_dot(code, format='png')
        display_png(stdout, raw=True)


_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(HierarchyMagic)
        _loaded = True
