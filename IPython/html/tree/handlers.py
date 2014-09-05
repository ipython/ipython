"""Tornado handlers for the tree view."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado import web
from ..base.handlers import IPythonHandler, notebook_path_regex, path_regex
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
    def get(self, path='', name=None):
        path = path.strip('/')
        cm = self.contents_manager
        if name is not None:
            # is a notebook, redirect to notebook handler
            url = url_escape(url_path_join(
                self.base_url, 'notebooks', path, name
            ))
            self.log.debug("Redirecting %s to %s", self.request.path, url)
            self.redirect(url)
        else:
            if not cm.path_exists(path=path):
                # Directory is hidden or does not exist.
                raise web.HTTPError(404)
            elif cm.is_hidden(path):
                self.log.info("Refusing to serve hidden directory, via 404 Error")
                raise web.HTTPError(404)
            breadcrumbs = self.generate_breadcrumbs(path)
            page_title = self.generate_page_title(path)
            self.write(self.render_template('tree.html',
                page_title=page_title,
                notebook_path=path,
                breadcrumbs=breadcrumbs
            ))


#-----------------------------------------------------------------------------
# URL to handler mappings
#-----------------------------------------------------------------------------


default_handlers = [
    (r"/tree%s" % notebook_path_regex, TreeHandler),
    (r"/tree%s" % path_regex, TreeHandler),
    (r"/tree", TreeHandler),
    ]
