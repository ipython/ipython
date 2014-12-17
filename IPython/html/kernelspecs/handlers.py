import hashlib
from tornado import web
from ..base.handlers import IPythonHandler
from ..services.kernelspecs.handlers import kernel_name_regex

class KernelSpecResourceHandler(web.StaticFileHandler, IPythonHandler):
    SUPPORTED_METHODS = ('GET', 'HEAD')

    def initialize(self):
        web.StaticFileHandler.initialize(self, path='')

    @web.authenticated
    def get(self, kernel_name, path, include_body=True):
        ksm = self.kernel_spec_manager
        try:
            self.root = ksm.get_kernel_spec(kernel_name).resource_dir
        except KeyError:
            raise web.HTTPError(404, u'Kernel spec %s not found' % kernel_name)
        self.log.debug("Serving kernel resource from: %s", self.root)
        return web.StaticFileHandler.get(self, path, include_body=include_body)

    @web.authenticated
    def head(self, kernel_name, path):
        self.get(kernel_name, path, include_body=False)

    def compute_etag(self):
        """Computes the etag header to be used for this request.

        By default uses a hash of the content written so far.

        May be overridden to provide custom etag implementations,
        or may return None to disable tornado's default etag support.
        """
        hasher = hashlib.sha1()
        for part in self._write_buffer:
            hasher.update(part)
        return '"%s"' % hasher.hexdigest()

default_handlers = [
    (r"/kernelspecs/%s/(?P<path>.*)" % kernel_name_regex, KernelSpecResourceHandler),
]
