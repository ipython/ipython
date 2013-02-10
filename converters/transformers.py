"""
Module that regroups transformer that woudl be applied to ipynb files
before going through the templating machinery.

It exposes convenient classes to inherit from to access configurability
as well as decorator to simplify tasks.
"""

from __future__ import print_function

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Unicode, Bool, Dict, List

from converters.config import GlobalConfigurable

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
                    worksheet.cells[index], other = self.cell_transform(cell, other, index)
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
        if fmt in ('png', 'jpg', 'pdf'):
            data = data.decode('base64')

        return figname, key, data


    def cell_transform(self, cell, other, count):
        if other.get('figures', None) is None :
            other['figures'] = {}
        for out in cell.get('outputs', []):
            for out_type in self.display_data_priority:
                if out.hasattr(out_type):
                    figname, key, data = self._new_figure(out[out_type], out_type, count)
                    out['key_'+out_type] = figname
                    other['figures'][key] = data
                    count = count+1
        return cell, other

class RevealHelpTransformer(ConfigurableTransformers):

    section_open = False
    subsection_open = False
    fragment_open = False

    def open_subsection(self):
        self.subsection_open = True
        return True

    def open_section(self):
        self.section_open = True
        return True

    def open_fragment(self):
        self.fragment_open = True
        return True

    # could probaly write those maybe_close/open
    # with a function functor
    def maybe_close_section(self):
        """return True is already open, false otherwise
        and change state to close
        """
        if self.section_open :
            self.section_open = False
            return True
        else :
            return False

    def maybe_open_section(self):
        """return True is already open, false otherwise
        and change state to close
        """
        if not self.section_open :
            self.section_open = True
            return True
        else :
            return False

    def maybe_open_subsection(self):
        """return True is already open, false otherwise
        and change state to close
        """
        if not self.subsection_open :
            self.subsection_open = True
            return True
        else :
            return False

    def maybe_close_subsection(self):
        """return True is already open, false otherwise
        and change state to close
        """
        if self.subsection_open :
            self.subsection_open = False
            return True
        else :
            return False

    def maybe_close_fragment(self):
        """return True is already open, false otherwise
        and change state to close
        """
        if self.fragment_open :
            self.fragment_open = False
            return True
        else :
            return False

    def cell_transform(self, cell, other, count):
        ctype = cell.metadata.get('slideshow', {}).get('slide_type', None)
        if ctype in [None, '-'] :
            cell.metadata.slideshow = {}
            cell.metadata.slideshow['slide_type'] = None
        elif ctype == 'fragment':
            cell.metadata.slideshow.close_fragment = self.maybe_close_fragment()
            cell.metadata.slideshow.close_subsection = False
            cell.metadata.slideshow.close_section = False

            cell.metadata.slideshow.open_section = self.maybe_open_section()
            cell.metadata.slideshow.open_subsection = self.maybe_open_subsection()
            cell.metadata.slideshow.open_fragment = self.open_fragment()

        elif ctype == 'subslide':
            cell.metadata.slideshow.close_fragment = self.maybe_close_fragment()
            cell.metadata.slideshow.close_subsection = self.maybe_close_subsection()
            cell.metadata.slideshow.close_section = False

            cell.metadata.slideshow.open_section = self.maybe_open_section()
            cell.metadata.slideshow.open_subsection = self.open_subsection()
            cell.metadata.slideshow.open_fragment = False
        elif ctype == 'slide':
            cell.metadata.slideshow.close_fragment = self.maybe_close_fragment()
            cell.metadata.slideshow.close_subsection = self.maybe_close_subsection()
            cell.metadata.slideshow.close_section = self.maybe_close_section()

            cell.metadata.slideshow.open_section = self.open_section()
            cell.metadata.slideshow.open_subsection = self.open_subsection()
            cell.metadata.slideshow.open_fragment = False
        return cell, other


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
            # our overrides:
            os.path.join(here, '..', 'css', 'static_html.css'),
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

