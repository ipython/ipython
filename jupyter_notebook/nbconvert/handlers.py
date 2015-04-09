"""Tornado handlers for nbconvert."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import io
import os
import zipfile

from tornado import web

from ..base.handlers import (
    IPythonHandler, FilesRedirectHandler,
    path_regex,
)
from IPython.nbformat import from_dict

from IPython.utils.py3compat import cast_bytes
from IPython.utils import text

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
    output_filename = os.path.splitext(name)[0] + resources['output_extension']
    zipf.writestr(output_filename, cast_bytes(output, 'utf-8'))
    for filename, data in output_files.items():
        zipf.writestr(os.path.basename(filename), data)
    zipf.close()

    handler.finish(buffer.getvalue())
    return True

def get_exporter(format, **kwargs):
    """get an exporter, raising appropriate errors"""
    # if this fails, will raise 500
    try:
        from IPython.nbconvert.exporters.export import exporter_map
    except ImportError as e:
        raise web.HTTPError(500, "Could not import nbconvert: %s" % e)
    
    try:
        Exporter = exporter_map[format]
    except KeyError:
        # should this be 400?
        raise web.HTTPError(404, u"No exporter for format: %s" % format)
    
    try:
        return Exporter(**kwargs)
    except Exception as e:
        raise web.HTTPError(500, "Could not construct Exporter: %s" % e)

class NbconvertFileHandler(IPythonHandler):

    SUPPORTED_METHODS = ('GET',)
    
    @web.authenticated
    def get(self, format, path):
        
        exporter = get_exporter(format, config=self.config, log=self.log)
        
        path = path.strip('/')
        model = self.contents_manager.get(path=path)
        name = model['name']
        if model['type'] != 'notebook':
            raise web.HTTPError(400, "Not a notebook: %s" % path)

        self.set_header('Last-Modified', model['last_modified'])

        try:
            output, resources = exporter.from_notebook_node(
                model['content'],
                resources={
                    "metadata": {
                        "name": name[:name.rfind('.')],
                        "modified_date": (model['last_modified']
                            .strftime(text.date_format))
                    }
                }
            )
        except Exception as e:
            raise web.HTTPError(500, "nbconvert failed: %s" % e)

        if respond_zip(self, name, output, resources):
            return

        # Force download if requested
        if self.get_argument('download', 'false').lower() == 'true':
            filename = os.path.splitext(name)[0] + resources['output_extension']
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
        exporter = get_exporter(format, config=self.config)
        
        model = self.get_json_body()
        name = model.get('name', 'notebook.ipynb')
        nbnode = from_dict(model['content'])
        
        try:
            output, resources = exporter.from_notebook_node(nbnode)
        except Exception as e:
            raise web.HTTPError(500, "nbconvert failed: %s" % e)

        if respond_zip(self, name, output, resources):
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
    (r"/nbconvert/%s" % _format_regex, NbconvertPostHandler),
    (r"/nbconvert/%s%s" % (_format_regex, path_regex),
         NbconvertFileHandler),
    (r"/nbconvert/html%s" % path_regex, FilesRedirectHandler),
]
