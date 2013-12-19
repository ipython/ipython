import os

from tornado import web

from ..base.handlers import IPythonHandler, notebook_path_regex
from IPython.nbformat.current import to_notebook_json
from IPython.nbconvert.exporters.export import exporter_map
from IPython.utils import tz


def has_resource_files(resources):
    output_files_dir = resources.get('output_files_dir', "")
    return bool(os.path.isdir(output_files_dir) and \
                    os.listdir(output_files_dir))

class NbconvertFileHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET',)
    
    @web.authenticated
    def get(self, format, path='', name=None):
        exporter = exporter_map[format](config=self.config)
        
        path = path.strip('/')
        os_path = self.notebook_manager.get_os_path(name, path)
        if not os.path.isfile(os_path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % name)

        info = os.stat(os_path)
        self.set_header('Last-Modified', tz.utcfromtimestamp(info.st_mtime))

        # Force download if requested
        if self.get_argument('download', 'false').lower() == 'true':
            filename = os.path.splitext(name)[0] + '.' + exporter.file_extension
            self.set_header('Content-Disposition',
                            'attachment; filename="%s"' % filename)
        
        # MIME type
        if exporter.output_mimetype:
            self.set_header('Content-Type',
                            '%s; charset=utf-8' % exporter.output_mimetype)

        output, resources = exporter.from_filename(os_path)
        
        # TODO: If there are resources, combine them into a zip file
        assert not has_resource_files(resources)
        
        self.finish(output)

class NbconvertPostHandler(IPythonHandler):
    SUPPORTED_METHODS = ('POST',)

    @web.authenticated 
    def post(self, format):
        exporter = exporter_map[format](config=self.config)
        
        model = self.get_json_body()
        nbnode = to_notebook_json(model['content'])
        
        # MIME type
        if exporter.output_mimetype:
            self.set_header('Content-Type',
            '%s; charset=utf-8' % exporter.output_mimetype)

        output, resources = exporter.from_notebook_node(nbnode)

        # TODO: If there are resources, combine them into a zip file
        assert not has_resource_files(resources)
        
        self.finish(output)

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

_format_regex = r"(?P<format>\w+)"


default_handlers = [
    (r"/nbconvert/%s%s" % (_format_regex, notebook_path_regex),
         NbconvertFileHandler),
    (r"/nbconvert/%s" % _format_regex, NbconvertPostHandler),
]