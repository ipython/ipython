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
