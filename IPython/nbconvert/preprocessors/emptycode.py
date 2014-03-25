"""Defines a preprocessor that removes the empty code cells from the exported notebook."""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

# Imports
from .base import Preprocessor

# Classes
class EmptyCodePreprocessor(Preprocessor):
    """Preprocessor that removes the empty code cells from the exported notebook."""

    def preprocess(self, nb, resources):
        """Preprocess a notebook."""
        self.log.debug("Applying preprocess: %s", self.__class__.__name__)
        for worksheet in nb.worksheets:
            # Rewrite the list of cells, excluding any empty code cells.
            worksheet.cells = [c for c in worksheet.cells if \
                not (c.cell_type == u'code' and not c.input.strip())]
        return nb, resources
