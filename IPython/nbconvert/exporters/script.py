"""Generic script exporter class for any kernel language"""

from .templateexporter import TemplateExporter

class ScriptExporter(TemplateExporter):
    def _template_file_default(self):
        return 'script'

    def from_notebook_node(self, nb, resources=None, **kw):
        langinfo = nb.metadata.get('language_info', {})
        self.file_extension = langinfo.get('file_extension', '.txt')
        self.output_mimetype = langinfo.get('mimetype', 'text/plain')

        return super(ScriptExporter, self).from_notebook_node(nb, resources, **kw)
