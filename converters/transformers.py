"""

"""

from __future__ import print_function

from IPython.config.configurable import Configurable
from IPython.utils.traitlets import Unicode, Bool, Dict, List

class ConfigurableTransformers(Configurable):
    """ A configurable transformer """

    def __init__(self, config=None, **kw):
        super(ConfigurableTransformers, self).__init__(config=config, **kw)

    def __call__(self, nb, other):
        try :
            for worksheet in nb.worksheets :
                for index, cell in enumerate(worksheet.cells):
                    worksheet.cells[index], other = self.cell_transform(cell, other, index)
            return nb, other
        except NotImplementedError as error :
            raise NotImplementedError('should be implemented by subclass')

    def cell_transform(self, cell, other, index):
        """
        Overwrite if you want to apply a transformation on each cell
        """
        raise NotImplementedError('should be implemented by subclass')


class Foobar(ConfigurableTransformers):
    message = Unicode('-- nothing', config=True)


    def cell_transform(self, cell, other, index):
        return cell, other


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


# todo, make the key part configurable.

class ExtractFigureTransformer(ConfigurableTransformers):
    enabled = Bool(False,
            config=True,
            help=""" If set to false, this transformer will be no-op """
            )

    extra_ext_map =  Dict({},
            config=True,
            help="""extra map to override extension based on type.
            Usefull for latex where svg will be converted to pdf before inclusion
            """
            )
    display_data_priority = List(['html', 'pdf', 'svg', 'latex', 'png', 'jpg', 'jpeg' , 'text'],
            config=True,
              help= """
                    An ordered list of prefered output type, the first
                    encounterd will usually be used when converting discarding
                    the others.
                    """
            )


    #to do change this to .format {} syntax
    key_tpl = Unicode('_fig_%02i.%s', config=True)

    def _get_ext(self, ext):
        if ext in self.extra_ext_map :
            return self.extra_ext_map[ext]
        return ext

    def _new_figure(self, data, fmt, count):
        """Create a new figure file in the given format.

        Returns a path relative to the input file.
        """
        figname = self.key_tpl % (count, self._get_ext(fmt))
        key     = self.key_tpl % (count, fmt)

        # Binary files are base64-encoded, SVG is already XML
        if fmt in ('png', 'jpg', 'pdf'):
            data = data.decode('base64')

        return figname, key, data


    def cell_transform(self, cell, other, count):
        if not self.enabled:
            return cell, other
        if other.get('figures',None) is None :
            other['figures']={}
        for i, out in enumerate(cell.get('outputs', [])):
            for type in self.display_data_priority:
                if out.hasattr(type):
                    figname, key, data = self._new_figure(out[type], type, count)
                    out['key_'+type] = figname
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

    def cell_transform(self, cell, other,count):
        ctype = cell.metadata.get('slideshow',{}).get('slide_type',None)
        if ctype is None :
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
        return cell,other

