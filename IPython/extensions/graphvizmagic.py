from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.core.magic_arguments import (argument, magic_arguments,
                                          parse_argstring)
from IPython.core.display import display_png, display_svg


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
class GraphvizMagic(Magics):

    @magic_arguments()
    @argument(
        '-f', '--format', default='png', choices=('png', 'svg'),
        help='output format (png/svg)'
    )
    @argument(
        'options', default=[], nargs='*',
        help='options passed to the `dot` command'
    )
    @cell_magic
    def dot(self, line, cell):
        """Draw a figure using Graphviz dot command."""
        args = parse_argstring(self.dot, line)

        image = run_dot(cell, args.options, format=args.format)

        if args.format == 'png':
            display_png(image, raw=True)
        elif args.format == 'svg':
            display_svg(image, raw=True)


_loaded = False

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    global _loaded
    if not _loaded:
        ip.register_magics(GraphvizMagic)
        _loaded = True
