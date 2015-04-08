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
        return self.get(kernel_name, path, include_body=False)

default_handlers = [
    (r"/kernelspecs/%s/(?P<path>.*)" % kernel_name_regex, KernelSpecResourceHandler),
]