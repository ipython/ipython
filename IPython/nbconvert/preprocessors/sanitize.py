"""
NBConvert Preprocessor for sanitizing HTML rendering of notebooks.
"""

from bleach import (
    ALLOWED_ATTRIBUTES,
    ALLOWED_STYLES,
    ALLOWED_TAGS,
    clean,
)
from IPython.utils.traitlets import (
    Any,
    Bool,
    List,
    Set,
    Unicode,
)
from IPython.nbconvert.preprocessors.base import Preprocessor


class SanitizeHTML(Preprocessor):

    # Bleach config.
    attributes = Any(
        config=True,
        default_value=ALLOWED_ATTRIBUTES,
        help="Allowed HTML tag attributes",
    )
    tags = List(
        Unicode,
        config=True,
        default=ALLOWED_TAGS,
        help="List of HTML tags to allow",
    )
    styles = List(
        Unicode,
        config=True,
        default_value=ALLOWED_STYLES,
        help="Allowed CSS styles if <style> tag is whitelisted"
    )
    strip = Bool(
        config=True,
        default_value=False,
        help="If True, remove unsafe markup entirely instead of escaping"
    )
    strip_comments = Bool(
        config=True,
        default_value=True,
        help="If True, strip comments from escaped HTML",
    )

    # Display data config.
    safe_output_keys = Set(
        config=True,
        default_value={
            'metadata',  # Not a mimetype per-se, but expected and safe.
            'text/plain',
            'text/latex',
            'application/json',
            'image/png',
            'image/jpeg',
        },
        help="Cell output mimetypes to render without modification",
    )
    sanitized_output_types = Set(
        config=True,
        default_value={
            'text/html',
            'text/markdown',
        },
        help="Cell output types to display after escaping with Bleach.",
    )

    def preprocess_cell(self, cell, resources, cell_index):
        """
        Sanitize dangerous contents of the cell.

        Cell Types:
          raw:
            Return unchanged
          markdown:
            Sanitize literal HTML
          code:
            Sanitize outputs that cou
        """
        if cell.cell_type == 'raw':
            return cell, resources
        elif cell.cell_type == 'markdown':
            cell.source = self.sanitize_html_tags(cell.source)
            return cell, resources
        elif cell.cell_type == 'code':
            cell.outputs = self.sanitize_code_outputs(cell.outputs)
            return cell, resources

    def sanitize_code_outputs(self, outputs):
        """
        Sanitize code cell outputs.

        Removes 'text/javascript' fields from display_data outputs, and
        runs `sanitize_html_tags` over 'text/html'.
        """
        for output in outputs:
            # These are always ascii, so nothing to escape.
            if output['output_type'] in ('stream', 'error'):
                continue
            data = output.data
            to_remove = []
            for key in data:
                if key in self.safe_output_keys:
                    continue
                elif key in self.sanitized_output_types:
                    self.log.info("Sanitizing %s" % key)
                    data[key] = self.sanitize_html_tags(data[key])
                else:
                    # Mark key for removal. (Python doesn't allow deletion of
                    # keys from a dict during iteration)
                    to_remove.append(key)
            for key in to_remove:
                self.log.info("Removing %s" % key)
                del data[key]
        return outputs

    def sanitize_html_tags(self, html_str):
        """
        Sanitize a string containing raw HTML tags.
        """
        return clean(
            html_str,
            tags=self.tags,
            attributes=self.attributes,
            styles=self.styles,
            strip=self.strip,
            strip_comments=self.strip_comments,
        )
