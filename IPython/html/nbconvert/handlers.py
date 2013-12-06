import os

from tornado import web

from ..base.handlers import IPythonHandler
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
        exporter = exporter_map[format]()
        
        path = path.strip('/')
        os_path = self.notebook_manager.get_os_path(name, path)
        if not os.path.isfile(os_path):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % name)

        info = os.stat(os_path)
        self.set_header('Last-Modified', tz.utcfromtimestamp(info.st_mtime))
        
        output, resources = exporter.from_filename(os_path)
        
        # TODO: If there are resources, combine them into a zip file
        assert not has_resource_files(resources)
        
        self.finish(output)

class NbconvertPostHandler(IPythonHandler):
    SUPPORTED_METHODS = ('POST',)

    @web.authenticated 
    def post(self, format):
        exporter = exporter_map[format]()
        
        model = self.get_json_body()
        nbnode = to_notebook_json(model['content'])
        output, resources = exporter.from_notebook_node(nbnode)
        
        # TODO: If there are resources, combine them into a zip file
        assert not has_resource_files(resources)
        
        self.finish(output)

#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------

_format_regex = r"(?P<format>\w+)"
_path_regex = r"(?P<path>(?:/.*)*)"
_notebook_name_regex = r"(?P<name>[^/]+\.ipynb)"
_notebook_path_regex = "%s/%s" % (_path_regex, _notebook_name_regex)

default_handlers = [
    (r"/nbconvert/%s%s" % (_format_regex, _notebook_path_regex),
         NbconvertFileHandler),
    (r"/nbconvert/%s" % _format_regex, NbconvertPostHandler),
]