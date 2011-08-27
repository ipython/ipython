"""Tornado handlers for the notebook.

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2011  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from tornado import web
from tornado import websocket

from zmq.eventloop import ioloop
from zmq.utils import jsonapi

from IPython.zmq.session import Session

try:
    from docutils.core import publish_string
except ImportError:
    publish_string = None



#-----------------------------------------------------------------------------
# Top-level handlers
#-----------------------------------------------------------------------------

class BaseHandler(web.RequestHandler):
    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        keyword = self.get_secure_cookie("keyword")
        if self.application.keyword and self.application.keyword != keyword:
            return None
        if not user_id:
            user_id = 'anonymous'
        return user_id

class NBBrowserHandler(BaseHandler):
    @web.authenticated
    def get(self):
        nbm = self.application.notebook_manager
        project = nbm.notebook_dir
        self.render('nbbrowser.html', project=project)

class LoginHandler(BaseHandler):
    def get(self):
        user_id = self.get_secure_cookie("user")
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name" value=%s>'
                   'Keyword: <input type="password" name="keyword">'
                   '<input type="submit" value="Sign in">'
                   '</form></body></html>'%user_id)

    def post(self):
        self.set_secure_cookie("user", self.get_argument("name", default=u''))
        self.set_secure_cookie("keyword", self.get_argument("keyword", default=u''))
        self.redirect("/")

class NewHandler(web.RequestHandler):
    def get(self):
        notebook_id = self.application.notebook_manager.new_notebook()
        self.render('notebook.html', notebook_id=notebook_id)


class NamedNotebookHandler(web.RequestHandler):
    def get(self, notebook_id):
        nbm = self.application.notebook_manager
        if not nbm.notebook_exists(notebook_id):
            raise web.HTTPError(404, u'Notebook does not exist: %s' % notebook_id)
        self.render('notebook.html', notebook_id=notebook_id)


#-----------------------------------------------------------------------------
# Kernel handlers
#-----------------------------------------------------------------------------


class MainKernelHandler(web.RequestHandler):

    def get(self):
        km = self.application.kernel_manager
        self.finish(jsonapi.dumps(km.kernel_ids))

    def post(self):
        km = self.application.kernel_manager
        notebook_id = self.get_argument('notebook', default=None)
        kernel_id = km.start_kernel(notebook_id)
        ws_url = self.application.ipython_app.get_ws_url()
        data = {'ws_url':ws_url,'kernel_id':kernel_id}
        self.set_header('Location', '/'+kernel_id)
        self.finish(jsonapi.dumps(data))


class KernelHandler(web.RequestHandler):

    SUPPORTED_METHODS = ('DELETE')

    def delete(self, kernel_id):
        km = self.application.kernel_manager
        km.kill_kernel(kernel_id)
        self.set_status(204)
        self.finish()


class KernelActionHandler(web.RequestHandler):

    def post(self, kernel_id, action):
        km = self.application.kernel_manager
        if action == 'interrupt':
            km.interrupt_kernel(kernel_id)
            self.set_status(204)
        if action == 'restart':
            new_kernel_id = km.restart_kernel(kernel_id)
            ws_url = self.application.ipython_app.get_ws_url()
            data = {'ws_url':ws_url,'kernel_id':new_kernel_id}
            self.set_header('Location', '/'+new_kernel_id)
            self.write(jsonapi.dumps(data))
        self.finish()


class ZMQStreamHandler(websocket.WebSocketHandler):

    def _reserialize_reply(self, msg_list):
        """Reserialize a reply message using JSON.

        This takes the msg list from the ZMQ socket, unserializes it using
        self.session and then serializes the result using JSON. This method
        should be used by self._on_zmq_reply to build messages that can
        be sent back to the browser.
        """
        idents, msg_list = self.session.feed_identities(msg_list)
        msg = self.session.unserialize(msg_list)
        try:
            msg['header'].pop('date')
        except KeyError:
            pass
        try:
            msg['parent_header'].pop('date')
        except KeyError:
            pass
        msg.pop('buffers')
        return jsonapi.dumps(msg)

    def _on_zmq_reply(self, msg_list):
        try:
            msg = self._reserialize_reply(msg_list)
        except:
            self.application.kernel_manager.log.critical("Malformed message: %r" % msg_list)
        else:
            self.write_message(msg)


class IOPubHandler(ZMQStreamHandler):

    def initialize(self, *args, **kwargs):
        self._kernel_alive = True
        self._beating = False
        self.iopub_stream = None
        self.hb_stream = None

    def open(self, kernel_id):
        km = self.application.kernel_manager
        self.kernel_id = kernel_id
        self.session = Session()
        self.time_to_dead = km.time_to_dead
        try:
            self.iopub_stream = km.create_iopub_stream(kernel_id)
            self.hb_stream = km.create_hb_stream(kernel_id)
        except web.HTTPError:
            # WebSockets don't response to traditional error codes so we
            # close the connection.
            if not self.stream.closed():
                self.stream.close()
        else:
            self.iopub_stream.on_recv(self._on_zmq_reply)
            self.start_hb(self.kernel_died)

    def on_close(self):
        # This method can be called twice, once by self.kernel_died and once 
        # from the WebSocket close event. If the WebSocket connection is
        # closed before the ZMQ streams are setup, they could be None.
        self.stop_hb()
        if self.iopub_stream is not None and not self.iopub_stream.closed():
            self.iopub_stream.on_recv(None)
            self.iopub_stream.close()
        if self.hb_stream is not None and not self.hb_stream.closed():
            self.hb_stream.close()
 
    def start_hb(self, callback):
        """Start the heartbeating and call the callback if the kernel dies."""
        if not self._beating:
            self._kernel_alive = True

            def ping_or_dead():
                if self._kernel_alive:
                    self._kernel_alive = False
                    self.hb_stream.send(b'ping')
                else:
                    try:
                        callback()
                    except:
                        pass
                    finally:
                        self._hb_periodic_callback.stop()

            def beat_received(msg):
                self._kernel_alive = True

            self.hb_stream.on_recv(beat_received)
            self._hb_periodic_callback = ioloop.PeriodicCallback(ping_or_dead, self.time_to_dead*1000)
            self._hb_periodic_callback.start()
            self._beating= True

    def stop_hb(self):
        """Stop the heartbeating and cancel all related callbacks."""
        if self._beating:
            self._hb_periodic_callback.stop()
            if not self.hb_stream.closed():
                self.hb_stream.on_recv(None)

    def kernel_died(self):
        self.application.kernel_manager.delete_mapping_for_kernel(self.kernel_id)
        self.write_message(
            {'header': {'msg_type': 'status'},
             'parent_header': {},
             'content': {'execution_state':'dead'}
            }
        )
        self.on_close()


class ShellHandler(ZMQStreamHandler):

    def initialize(self, *args, **kwargs):
        self.shell_stream = None

    def open(self, kernel_id):
        km = self.application.kernel_manager
        self.max_msg_size = km.max_msg_size
        self.kernel_id = kernel_id
        try:
            self.shell_stream = km.create_shell_stream(kernel_id)
        except web.HTTPError:
            # WebSockets don't response to traditional error codes so we
            # close the connection.
            if not self.stream.closed():
                self.stream.close()
        else:
            self.session = Session()
            self.shell_stream.on_recv(self._on_zmq_reply)

    def on_message(self, msg):
        if len(msg) < self.max_msg_size:
            msg = jsonapi.loads(msg)
            self.session.send(self.shell_stream, msg)

    def on_close(self):
        # Make sure the stream exists and is not already closed.
        if self.shell_stream is not None and not self.shell_stream.closed():
            self.shell_stream.close()


#-----------------------------------------------------------------------------
# Notebook web service handlers
#-----------------------------------------------------------------------------

class NotebookRootHandler(web.RequestHandler):

    def get(self):
        nbm = self.application.notebook_manager
        files = nbm.list_notebooks()
        self.finish(jsonapi.dumps(files))

    def post(self):
        nbm = self.application.notebook_manager
        body = self.request.body.strip()
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        if body:
            notebook_id = nbm.save_new_notebook(body, name=name, format=format)
        else:
            notebook_id = nbm.new_notebook()
        self.set_header('Location', '/'+notebook_id)
        self.finish(jsonapi.dumps(notebook_id))


class NotebookHandler(web.RequestHandler):

    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')

    def get(self, notebook_id):
        nbm = self.application.notebook_manager
        format = self.get_argument('format', default='json')
        last_mod, name, data = nbm.get_notebook(notebook_id, format)
        if format == u'json':
            self.set_header('Content-Type', 'application/json')
            self.set_header('Content-Disposition','attachment; filename="%s.ipynb"' % name)
        elif format == u'py':
            self.set_header('Content-Type', 'application/x-python')
            self.set_header('Content-Disposition','attachment; filename="%s.py"' % name)
        self.set_header('Last-Modified', last_mod)
        self.finish(data)

    def put(self, notebook_id):
        nbm = self.application.notebook_manager
        format = self.get_argument('format', default='json')
        name = self.get_argument('name', default=None)
        nbm.save_notebook(notebook_id, self.request.body, name=name, format=format)
        self.set_status(204)
        self.finish()

    def delete(self, notebook_id):
        nbm = self.application.notebook_manager
        nbm.delete_notebook(notebook_id)
        self.set_status(204)
        self.finish()

#-----------------------------------------------------------------------------
# RST web service handlers
#-----------------------------------------------------------------------------


class RSTHandler(web.RequestHandler):

    def post(self):
        if publish_string is None:
            raise web.HTTPError(503, u'docutils not available')
        body = self.request.body.strip()
        source = body
        # template_path=os.path.join(os.path.dirname(__file__), u'templates', u'rst_template.html')
        defaults = {'file_insertion_enabled': 0,
                    'raw_enabled': 0,
                    '_disable_config': 1,
                    'stylesheet_path': 0
                    # 'template': template_path
        }
        try:
            html = publish_string(source, writer_name='html',
                                  settings_overrides=defaults
            )
        except:
            raise web.HTTPError(400, u'Invalid RST')
        print html
        self.set_header('Content-Type', 'text/html')
        self.finish(html)


