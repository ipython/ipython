"""NotebookExporter class"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .exporter import Exporter
from IPython import nbformat
from IPython.utils.traitlets import Enum

class NotebookExporter(Exporter):
    """Exports to an IPython notebook."""

    nbformat_version = Enum(list(nbformat.versions),
        default_value=nbformat.current_nbformat,
        config=True,
        help="""The nbformat version to write.
        Use this to downgrade notebooks.
        """
    )
    def _file_extension_default(self):
        return '.ipynb'

    output_mimetype = 'application/json'

    def from_notebook_node(self, nb, resources=None, **kw):
        nb_copy, resources = super(NotebookExporter, self).from_notebook_node(nb, resources, **kw)
        if self.nbformat_version != nb_copy.nbformat:
            resources['output_suffix'] = '.v%i' % self.nbformat_version
        else:
            resources['output_suffix'] = '.nbconvert'
        output = nbformat.writes(nb_copy, version=self.nbformat_version)
        return output, resources
