"""NotebookExporter class"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from .exporter import Exporter
from IPython.nbformat import current as nbformat

class NotebookExporter(Exporter):
    """
    Exports an IPython notebook.
    """
    def _file_extension_default(self):
        return 'ipynb'

    output_mimetype = 'application/json'

    def from_notebook_node(self, nb, resources=None, **kw):
        nb_copy, resources = super(NotebookExporter, self).from_notebook_node(nb, resources, **kw)
        output = nbformat.writes_json(nb_copy)
        return output, resources
