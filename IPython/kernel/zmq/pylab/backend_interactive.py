"""
Displays Agg images in the browser, with interactivity
"""
from __future__ import division, print_function

import datetime
import errno
import io
import json
import os
import random
import socket
import mimetypes

import numpy as np

import tornado
import tornado.web
import tornado.ioloop
import tornado.websocket
import tornado.template

import matplotlib
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.backends import backend_agg
from matplotlib import backend_bases
from matplotlib._pylab_helpers import Gcf
from matplotlib import _png

from IPython.display import display_html, display_javascript

# exposed interfaces

def show():
    """
    For image backends - is not required
    For GUI backends - show() is usually the last line of a pylab script and
    tells the backend that it is time to draw.  In interactive mode, this may
    be a do nothing func.  See the GTK backend for an example of how to handle
    interactive versus batch mode
    """
    for manager in show._managers_to_show:
        manager.show()
    show._managers_to_show.clear()

# list of figures to draw when flush_figures is called
show._managers_to_show = set()

def draw_if_interactive():
    """
    Is called after every pylab drawing command
    """
    if matplotlib.is_interactive():
        manager = Gcf.get_active()
        if manager is not None:
            manager.canvas.draw_idle()
            show._managers_to_show.add(manager)

def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)
    return new_figure_manager_given_figure(num, thisFig)


def new_figure_manager_given_figure(num, figure):
    """
    Create a new figure manager instance for the given figure.
    """
    canvas = FigureCanvasWebAgg(figure)
    manager = FigureManagerWebAgg(canvas, num)
    return manager


class TimerTornado(backend_bases.TimerBase):
    def _timer_start(self):
        self._timer_stop()
        if self._single:
            ioloop = tornado.ioloop.IOLoop.instance()
            self._timer = ioloop.add_timeout(
                datetime.timedelta(milliseconds=self.interval),
                self._on_timer)
        else:
            self._timer = tornado.ioloop.PeriodicCallback(
                self._on_timer,
                self.interval)
        self._timer.start()

    def _timer_stop(self):
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def _timer_set_interval(self):
        # Only stop and restart it if the timer has already been started
        if self._timer is not None:
            self._timer_stop()
            self._timer_start()


class FigureCanvasWebAgg(backend_agg.FigureCanvasAgg):
    supports_blit = False

    def __init__(self, *args, **kwargs):
        super(FigureCanvasWebAgg, self).__init__(*args, **kwargs)

        # backend_agg.FigureCanvasAgg.__init__(self, *args, **kwargs)

        # A buffer to hold the PNG data for the last frame.  This is
        # retained so it can be resent to each client without
        # regenerating it.
        self._png_buffer = io.BytesIO()

        # Set to True when the renderer contains data that is newer
        # than the PNG buffer.
        self._png_is_old = True

        # Set to True by the `refresh` message so that the next frame
        # sent to the clients will be a full frame.
        self._force_full = True

        # Set to True when a drawing is in progress to prevent redraw
        # messages from piling up.
        self._pending_draw = None

    def draw(self):
        # TODO: Do we just queue the drawing here?  That's what Gtk does
        renderer = self.get_renderer()

        self._png_is_old = True

        backend_agg.RendererAgg.lock.acquire()
        try:
            self.figure.draw(renderer)
        finally:
            backend_agg.RendererAgg.lock.release()
            # Swap the frames
            self.manager.refresh_all()

    def draw_idle(self):
        if self._pending_draw is None:
            ioloop = tornado.ioloop.IOLoop.instance()
            self._pending_draw = ioloop.add_timeout(
                datetime.timedelta(milliseconds=50),
                self._draw_idle_callback)

    def _draw_idle_callback(self):
        try:
            self.draw()
        finally:
            self._pending_draw = None

    def get_diff_image(self):
        if self._png_is_old:
            # The buffer is created as type uint32 so that entire
            # pixels can be compared in one numpy call, rather than
            # needing to compare each plane separately.
            buff = np.frombuffer(self._renderer.buffer_rgba(), dtype=np.uint32)
            buff.shape = (self._renderer.height, self._renderer.width)

            if not self._force_full:
                last_buffer = np.frombuffer(self._last_renderer.buffer_rgba(), dtype=np.uint32)
                last_buffer.shape = (self._renderer.height, self._renderer.width)

                diff = buff != last_buffer
                output = np.where(diff, buff, 0)
            else:
                output = buff

            # Clear out the PNG data buffer rather than recreating it
            # each time.  This reduces the number of memory
            # (de)allocations.
            self._png_buffer.truncate()
            self._png_buffer.seek(0)

            # TODO: We should write a new version of write_png that
            # handles the differencing inline
            _png.write_png(
                output.tostring(),
                output.shape[1], output.shape[0],
                self._png_buffer)

            # Swap the renderer frames
            self._renderer, self._last_renderer = self._last_renderer, self._renderer
            self._force_full = False
            self._png_is_old = False
        return self._png_buffer.getvalue()

    def get_renderer(self, cleared=False):
        # Mirrors super.get_renderer, but caches the old one
        # so that we can do things such as prodce a diff image
        # in get_diff_image
        _, _, w, h = self.figure.bbox.bounds
        key = w, h, self.figure.dpi
        try:
            self._lastKey, self._renderer
        except AttributeError:
            need_new_renderer = True
        else:
            need_new_renderer = (self._lastKey != key)

        if need_new_renderer:
            self._renderer = backend_agg.RendererAgg(
                w, h, self.figure.dpi)
            self._last_renderer = backend_agg.RendererAgg(
                w, h, self.figure.dpi)
            self._lastKey = key

        return self._renderer

    def handle_event(self, event):
        e_type = event['type']
        if e_type in ('button_press', 'button_release', 'motion_notify'):
            x = event['x']
            y = event['y']
            y = self.get_renderer().height - y

            # Javascript button numbers and matplotlib button numbers are
            # off by 1
            button = event['button'] + 1

            # The right mouse button pops up a context menu, which
            # doesn't work very well, so use the middle mouse button
            # instead.  It doesn't seem that it's possible to disable
            # the context menu in recent versions of Chrome.
            if button == 2:
                button = 3

            if e_type == 'button_press':
                self.button_press_event(x, y, button)
            elif e_type == 'button_release':
                self.button_release_event(x, y, button)
            elif e_type == 'motion_notify':
                self.motion_notify_event(x, y)
        elif e_type in ('key_press', 'key_release'):
            key = event['key']

            if e_type == 'key_press':
                self.key_press_event(key)
            elif e_type == 'key_release':
                self.key_release_event(key)
        elif e_type == 'toolbar_button':
            self.toolbar.handle_event(event)
        elif e_type == 'refresh':
            self._force_full = True
            self.draw_idle()

    def send_event(self, event_type, **kwargs):
        self.manager.send_event(event_type, **kwargs)

    def new_timer(self, *args, **kwargs):
        return TimerTornado(*args, **kwargs)

class FigureManagerWebAgg(backend_bases.FigureManagerBase):
    def __init__(self, canvas, num):
        backend_bases.FigureManagerBase.__init__(self, canvas, num)
        self.web_sockets = set()
        self.toolbar = self._get_toolbar(canvas)

    # overrides FigureManagerBase
    def show(self):
        global iframe_resizing_script_injected # module global
        if not iframe_resizing_script_injected:
            display_javascript(iframe_resizing_script.format(figure_domain = domain), raw = True)
            iframe_resizing_script_injected = True

        number = self.canvas.figure.number
        url = "{0}/{1}".format(domain, number)
        # 50px to allow for the message, etc. of course a better solution is needed
        iframe = '<iframe id="iframe-{number}" src="{src}" frameborder="0" width="100%"></iframe>'
        display_html(iframe.format(number = number, src = url), raw = True)

    # overrides FigureManagerBase
    def resize(self, w, h):
        self.send_event('resize', size=(w, h))

    # our stuff
    def add_web_socket(self, web_socket):
        self.web_sockets.add(web_socket)

    def remove_web_socket(self, web_socket):
        if web_socket in self.web_sockets:
            self.web_sockets.remove(web_socket)

    def refresh_all(self):
        if self.web_sockets:
            diff = self.canvas.get_diff_image()
            for s in self.web_sockets:
                s.send_diff_image(diff)

    def send_event(self, event_type, **kwargs):
        for s in self.web_sockets:
            s.send_event(event_type, **kwargs)

    def _get_toolbar(self, canvas):
        toolbar = NavigationToolbar2WebAgg(canvas)
        return toolbar


class NavigationToolbar2WebAgg(backend_bases.NavigationToolbar2):
    def _init_toolbar(self):
        self.event_handlers = ("home", "back", "forward", "pan", "zoom")

        self.toolitems = tuple(filter(lambda x: x[3] in self.event_handlers,
            backend_bases.NavigationToolbar2.toolitems))

        self.message = ''
        self.cursor = 0

    # overrides
    def draw_rubberband(self, event, x0, y0, x1, y1):
        self.canvas.send_event("rubberband", x0=x0, y0=y0, x1=x1, y1=y1)

    def dynamic_update(self):
        self.canvas.draw_idle()

    def release_zoom(self, event):
        super(NavigationToolbar2WebAgg, self).release_zoom(event)
        self.canvas.send_event("rubberband", x0=-1, y0=-1, x1=-1, y1=-1)

    def set_cursor(self, cursor):
        if cursor != self.cursor:
            self.canvas.send_event("cursor", cursor=cursor)
        self.cursor = cursor

    def set_message(self, message):
        if message != self.message:
            self.canvas.send_event("message", message=message)
        self.message = message

    def _get_canvas(self, fig):
        return FigureCanvasWebAgg(fig)

    def handle_event(self, event):
        name = event['name'] 
        if name in self.event_handlers:
            getattr(self, name)()

class SingleFigurePage(tornado.web.RequestHandler):
    def get(self, fignum):
        manager = Gcf.get_fig_manager(int(fignum))
        if not manager:
            raise tornado.web.HTTPError(404)
        self.render("figure.html", canvas = manager.canvas)

class Download(tornado.web.RequestHandler):
    def get(self, fignum, fmt):
        manager = Gcf.get_fig_manager(int(fignum))
        if not manager:
            raise tornado.web.HTTPError(404)

        content_type = mimetypes.types_map.get('.' + fmt, 'application/binary')
        self.set_header('Content-Type', content_type)

        buff = io.BytesIO()
        manager.canvas.print_figure(buff, format=fmt)
        self.write(buff.getvalue())

class WebSocket(tornado.websocket.WebSocketHandler):
    def open(self, fignum):
        self.fignum = int(fignum)
        manager = Gcf.get_fig_manager(self.fignum)
        if not manager:
            raise tornado.web.HTTPError(404)

        manager.add_web_socket(self)
        _, _, w, h = manager.canvas.figure.bbox.bounds
        manager.resize(w, h)
        self.on_message('{"type":"refresh"}')
        if hasattr(self, 'set_nodelay'):
            self.set_nodelay(True)

    def on_close(self):
        manager = Gcf.get_fig_manager(self.fignum)
        if manager:
            manager.remove_web_socket(self)

    def on_message(self, message):
        message = json.loads(message)
        if message['type'] == 'ack':
            # Network latency tends to decrease if traffic is
            # flowing in both directions.  Therefore, the browser
            # sends back an "ack" message after each image frame
            # is received.  This could also be used as a simple
            # sanity check in the future, but for now the
            # performance increase is enough to justify it, even
            # if the server does nothing with it.
            pass
        else:
            manager = Gcf.get_fig_manager(self.fignum)
            if manager: # the figure might have been deleted in the meantime
                manager.canvas.handle_event(message)

    def send_event(self, event_type, **kwargs):
        payload = {'type': event_type}
        payload.update(kwargs)
        self.write_message(json.dumps(payload))

    def send_diff_image(self, diff):
        self.write_message(diff, binary=True)

class WebAggApplication(tornado.web.Application):
    def __init__(self):
        static_path = os.path.join(os.path.dirname(__file__), 'backend_interactive')

        settings = {
            'static_path': static_path,
            'static_url_prefix': '/_static/',
            'template_path': static_path
        }

        handlers = [
            (r'/([0-9]+)', SingleFigurePage),
            (r'/([0-9]+)/ws', WebSocket),
            (r'/([0-9]+)/download.([a-z]+)', Download),
        ]

        super(WebAggApplication, self).__init__(handlers, **settings)

    def log_request(self, handler):
        pass

# the module works well as a singleton

from tornado.httpserver import HTTPServer
application = WebAggApplication()
server = HTTPServer(application)
server.listen(0, address = "127.0.0.1") # this binds on a random port

# this is an hackish way of getting the socket the server is listening to
# maybe we should create our own socket

port = server._sockets.values()[0].getsockname()[1]

initialized = True
domain = "http://127.0.0.1:{port}".format(port = port)

iframe_resizing_script = """
function receiveMessage(event) {{
    // only accept messages from the specified domain
    if (event.origin !== "{figure_domain}") return;
    var iframe_id = event.data.iframe_id,
        iframe_height = event.data.iframe_height;
    if (isNaN(iframe_height)) return;
    var iframe = document.getElementById(iframe_id);
    iframe.height = iframe_height + "px";
}}
window.addEventListener("message", receiveMessage, false);
"""

iframe_resizing_script_injected = False

rcParams.update({
    'figure.figsize': (6.0,4.0),
    # play nicely with white background in the Qt and notebook frontend
    'figure.facecolor': 'white',
    'figure.edgecolor': 'white',
    # 12pt labels get cutoff on 6x4 logplots, so use 10pt.
    'font.size': 10,
    # 72 dpi matches SVG/qtconsole
    # this only affects PNG export, as SVG has no dpi setting
    'savefig.dpi': 72,
    # 10pt still needs a little more room on the xlabel:
    'figure.subplot.bottom' : .125
})