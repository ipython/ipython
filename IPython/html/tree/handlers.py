"""Tornado handlers for the tree view."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web
from ..base.handlers import IPythonHandler, path_regex
from ..utils import url_path_join, url_escape


class TreeHandler(IPythonHandler):
    """Render the tree view, listing notebooks, clusters, etc."""

    def generate_breadcrumbs(self, path):
        breadcrumbs = [(url_escape(url_path_join(self.base_url, 'tree')), '')]
        comps = path.split('/')
        ncomps = len(comps)
        for i in range(ncomps):
            if comps[i]:
                link = url_escape(url_path_join(self.base_url, 'tree', *comps[0:i+1]))
                breadcrumbs.append((link, comps[i]))
        return breadcrumbs

    def generate_page_title(self, path):
        comps = path.split('/')
        if len(comps) > 3:
            for i in range(len(comps)-2):
                comps.pop(0)
        page_title = url_path_join(*comps)
        if page_title:
            return page_title+'/'
        else:
            return 'Home'

    @web.authenticated
    def get(self, path=''):
        path = path.strip('/')
        cm = self.contents_manager
        if cm.dir_exists(path=path):
            if cm.is_hidden(path):
                self.log.info("Refusing to serve hidden directory, via 404 Error")
                raise web.HTTPError(404)
            breadcrumbs = self.generate_breadcrumbs(path)
            page_title = self.generate_page_title(path)
            self.write(self.render_template('tree.html',
                page_title=page_title,
                notebook_path=path,
                breadcrumbs=breadcrumbs,
                terminals_available=self.settings['terminals_available'],
            ))
        elif cm.file_exists(path):
            # it's not a directory, we have redirecting to do
            model = cm.get(path, content=False)
            # redirect to /api/notebooks if it's a notebook, otherwise /api/files
            service = 'notebooks' if model['type'] == 'notebook' else 'files'
            url = url_escape(url_path_join(
                self.base_url, service, path,
            ))
            self.log.debug("Redirecting %s to %s", self.request.path, url)
            self.redirect(url)
        else:
            raise web.HTTPError(404)


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/tree%s" % path_regex, TreeHandler),
    (r"/tree", TreeHandler),
    ]
