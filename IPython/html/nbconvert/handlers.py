import io
import os
import zipfile

from tornado import web

from ..base.handlers import IPythonHandler, notebook_path_regex
from IPython.nbformat.current import to_notebook_json
from IPython.nbconvert.exporters.export import exporter_map
from IPython.utils import tz
from IPython.utils.py3compat import cast_bytes

import sys

def find_resource_files(output_files_dir):
    files = []
    for dirpath, dirnames, filenames in os.walk(output_files_dir):
        files.extend([os.path.join(dirpath, f) for f in filenames])
    return files

def respond_zip(handler, name, output, resources):
    """Zip up the output and resource files and respond with the zip file.

    Returns True if it has served a zip file, False if there are no resource
    files, in which case we serve the plain output file.
    """
    # Check if we have resource files we need to zip
    output_files = resources.get('outputs', None)
    if not output_files:
        return False

    # Headers
    zip_filename = os.path.splitext(name)[0] + '.zip'
    handler.set_header('Content-Disposition',
                       'attachment; filename="%s"' % zip_filename)
    handler.set_header('Content-Type', 'application/zip')

    # Prepare the zip file
    buffer = io.BytesIO()
    zipf = zipfile.ZipFile(buffer, mode='w', compression=zipfile.ZIP_DEFLATED)
    output_filename = os.path.splitext(name)[0] + '.' + resources['output_extension']
    zipf.writestr(output_filename, cast_bytes(output, 'utf-8'))
    for filename, data in output_files.items():
        zipf.writestr(os.path.basename(filename), data)
    zipf.close()

    handler.finish(buffer.getvalue())
    return True

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

        output, resources = exporter.from_filename(os_path)

        if respond_zip(self, name, output, resources):
            return

        # Force download if requested
        if self.get_argument('download', 'false').lower() == 'true':
            filename = os.path.splitext(name)[0] + '.' + resources['output_extension']
            self.set_header('Content-Disposition',
                               'attachment; filename="%s"' % filename)

        # MIME type
        if exporter.output_mimetype:
            self.set_header('Content-Type',
                            '%s; charset=utf-8' % exporter.output_mimetype)

        self.finish(output)

class NbconvertPostHandler(IPythonHandler):
    SUPPORTED_METHODS = ('POST',)

    @web.authenticated 
    def post(self, format):
        exporter = exporter_map[format](config=self.config)
        
        model = self.get_json_body()
        nbnode = to_notebook_json(model['content'])

        output, resources = exporter.from_notebook_node(nbnode)

        if respond_zip(self, nbnode.metadata.name, output, resources):
            return

        # MIME type
        if exporter.output_mimetype:
            self.set_header('Content-Type',
                            '%s; charset=utf-8' % exporter.output_mimetype)

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