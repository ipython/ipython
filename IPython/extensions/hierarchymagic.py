from IPython.core.magic import Magics, magics_class, line_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)
from IPython.core.display import display_png

from sphinx.ext.inheritance_diagram import InheritanceGraph


def run_dot(code, options=[], format='png'):
    # mostly copied from sphinx.ext.graphviz.render_dot
    from subprocess import Popen, PIPE
    from sphinx.util.osutil import EPIPE, EINVAL

    dot_args = ['dot'] + options + ['-T', format]
    p = Popen(dot_args, stdout=PIPE, stdin=PIPE, stderr=PIPE)
    wentwrong = False
    try:
        # Graphviz may close standard input when an error occurs,
        # resulting in a broken pipe on communicate()
        stdout, stderr = p.communicate(code)
    except (OSError, IOError), err:
        if err.errno != EPIPE:
            raise
        wentwrong = True
    except IOError, err:
        if err.errno != EINVAL:
            raise
        wentwrong = True
    if wentwrong:
        # in this case, read the standard output and standard error streams
        # directly, to get the error message(s)
        stdout, stderr = p.stdout.read(), p.stderr.read()
        p.wait()
    if p.returncode != 0:
        raise RuntimeError('dot exited with error:\n[stderr]\n{0}'
                           .format(stderr))
    return stdout


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
