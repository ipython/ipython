"""
Module that regroups transformer that woudl be applied to ipynb files
before going through the templating machinery.

It exposes convenient classes to inherit from to access configurability
as well as decorator to simplify tasks.
"""

from __future__ import print_function, absolute_import

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Unicode, Bool, Dict, List

from .config import GlobalConfigurable

class ConfigurableTransformers(GlobalConfigurable):
    """ A configurable transformer

    Inherit from this class if you wish to have configurability for your
    transformer.

    Any configurable traitlets this class exposed will be configurable in profiles
    using c.SubClassName.atribute=value

    you can overwrite cell_transform to apply a transformation independently on each cell
    or __call__ if you prefer your own logic. See orresponding docstring for informations.


    """

    def __init__(self, config=None, **kw):
        super(ConfigurableTransformers, self).__init__(config=config, **kw)

    def __call__(self, nb, other):
        """transformation to apply on each notebook.

        received a handle to the current notebook as well as a dict of resources
        which structure depends on the transformer.

        You should return modified nb, other.

        If you wish to apply on each cell, you might want to overwrite cell_transform method.
        """
        try :
            for worksheet in nb.worksheets :
                for index, cell in enumerate(worksheet.cells):
                    worksheet.cells[index], other = self.cell_transform(cell, other, 100*index)
            return nb, other
        except NotImplementedError:
            raise NotImplementedError('should be implemented by subclass')

    def cell_transform(self, cell, other, index):
        """
        Overwrite if you want to apply a transformation on each cell,

        receive the current cell, the resource dict and the index of current cell as parameter.

        You should return modified cell and resource dict.
        """
        raise NotImplementedError('should be implemented by subclass')
        return cell, other


class ActivatableTransformer(ConfigurableTransformers):
    """A simple ConfigurableTransformers that have an enabled flag

    Inherit from that if you just want to have a transformer which is
    no-op by default but can be activated in profiles with

    c.YourTransformerName.enabled = True
    """

    enabled = Bool(False, config=True)

    def __call__(self, nb, other):
        if not self.enabled :
            return nb, other
        else :
            return super(ActivatableTransformer, self).__call__(nb, other)


def cell_preprocessor(function):
    """ wrap a function to be executed on all cells of a notebook

    wrapped function  parameters :
        cell  : the cell
        other : external resources
        index : index of the cell
    """
    def wrappedfunc(nb, other):
        for worksheet in nb.worksheets :
            for index, cell in enumerate(worksheet.cells):
                worksheet.cells[index], other = function(cell, other, index)
        return nb, other
    return wrappedfunc


@cell_preprocessor
def haspyout_transformer(cell, other, count):
    """
    Add a haspyout flag to cell that have it

    Easier for templating, where you can't know in advance
    wether to write the out prompt

    """
    cell.type = cell.cell_type
    cell.haspyout = False
    for out in cell.get('outputs', []):
        if out.output_type == 'pyout':
            cell.haspyout = True
            break
    return cell, other

@cell_preprocessor
def coalesce_streams(cell, other, count):
    """merge consecutive sequences of stream output into single stream

    to prevent extra newlines inserted at flush calls

    TODO: handle \r deletion
    """
    outputs = cell.get('outputs', [])
    if not outputs:
        return cell, other
    new_outputs = []
    last = outputs[0]
    new_outputs = [last]
    for output in outputs[1:]:
        if (output.output_type == 'stream' and
            last.output_type == 'stream' and
            last.stream == output.stream
        ):
            last.text += output.text
        else:
            new_outputs.append(output)

    cell.outputs = new_outputs
    return cell, other

class ExtractFigureTransformer(ActivatableTransformer):


    extra_ext_map =  Dict({},
            config=True,
            help="""extra map to override extension based on type.
            Usefull for latex where svg will be converted to pdf before inclusion
            """
            )

    key_format_map =  Dict({},
            config=True,
            )

    figname_format_map =  Dict({},
            config=True,
            )


    #to do change this to .format {} syntax
    default_key_tpl = Unicode('_fig_{count:02d}.{ext}', config=True)

    def _get_ext(self, ext):
        if ext in self.extra_ext_map :
            return self.extra_ext_map[ext]
        return ext

    def _new_figure(self, data, fmt, count):
        """Create a new figure file in the given format.

        """
        tplf = self.figname_format_map.get(fmt, self.default_key_tpl)
        tplk = self.key_format_map.get(fmt, self.default_key_tpl)

        # option to pass the hash as data ?
        figname = tplf.format(count=count, ext=self._get_ext(fmt))
        key     = tplk.format(count=count, ext=self._get_ext(fmt))

        # Binary files are base64-encoded, SVG is already XML
        binary = False
        if fmt in ('png', 'jpg', 'pdf'):
            data = data.decode('base64')
            binary = True

        return figname, key, data, binary


    def cell_transform(self, cell, other, count):
        if other.get('figures', None) is None :
            other['figures'] = {'text':{},'binary':{}}
        for out in cell.get('outputs', []):
            for out_type in self.display_data_priority:
                if out.hasattr(out_type):
                    figname, key, data, binary = self._new_figure(out[out_type], out_type, count)
                    out['key_'+out_type] = figname
                    if binary :
                        other['figures']['binary'][key] = data
                    else :
                        other['figures']['text'][key] = data
                    count = count+1
        return cell, other


class RevealHelpTransformer(ConfigurableTransformers):

    def __call__(self, nb, other):
        for worksheet in nb.worksheets :
            for i, cell in enumerate(worksheet.cells):
                if not cell.get('metadata', None):
                    break
                cell.metadata.slide_type = cell.metadata.get('slideshow', {}).get('slide_type', None)
                if cell.metadata.slide_type is None:
                    cell.metadata.slide_type = '-'
                if cell.metadata.slide_type in ['slide']:
                    worksheet.cells[i - 1].metadata.slide_helper = 'slide_end'
                if cell.metadata.slide_type in ['subslide']:
                    worksheet.cells[i - 1].metadata.slide_helper = 'subslide_end'
        return nb, other


class CSSHtmlHeaderTransformer(ActivatableTransformer):

    def __call__(self, nb, resources):
        """Fetch and add css to the resource dict

        Fetch css from IPython adn Pygment to add at the beginning
        of the html files.

        Add this css in resources in the "inlining.css" key
        """
        resources['inlining'] = {}
        resources['inlining']['css'] = self.header
        return nb, resources

    header = []

    def __init__(self, config=None, **kw):
        super(CSSHtmlHeaderTransformer, self).__init__(config=config, **kw)
        if self.enabled :
            self.regen_header()

    def regen_header(self):
        ## lazy load asa this might not be use in many transformers
        import os
        from IPython.utils import path
        import io
        from pygments.formatters import HtmlFormatter
        header = []
        static = os.path.join(path.get_ipython_package_dir(),
            'frontend', 'html', 'notebook', 'static',
        )
        here = os.path.split(os.path.realpath(__file__))[0]
        css = os.path.join(static, 'css')
        for sheet in [
            # do we need jquery and prettify?
            # os.path.join(static, 'jquery', 'css', 'themes', 'base',
            # 'jquery-ui.min.css'),
            # os.path.join(static, 'prettify', 'prettify.css'),
            os.path.join(css, 'boilerplate.css'),
            os.path.join(css, 'fbm.css'),
            os.path.join(css, 'notebook.css'),
            os.path.join(css, 'renderedhtml.css'),
            os.path.join(css, 'style.min.css'),
        ]:
            try:
                with io.open(sheet, encoding='utf-8') as f:
                    s = f.read()
                    header.append(s)
            except IOError:
                # new version of ipython with style.min.css, pass
                pass

        pygments_css = HtmlFormatter().get_style_defs('.highlight')
        header.append(pygments_css)
        self.header = header

