 

class CSSHtmlHeaderTransformer(ActivatableTransformer):

    def __call__(self, nb, resources):
        """Fetch and add css to the resource dict

        Fetch css from IPython adn Pygment to add at the beginning
        of the html files.

        Add this css in resources in the "inlining.css" key
        """
        resources['inlining'] = {}
        resources['inlining']['css'] = self.header
        return nb, resources

    header = []

    def __init__(self, config=None, **kw):
        super(CSSHtmlHeaderTransformer, self).__init__(config=config, **kw)
        if self.enabled :
            self.regen_header()

    def regen_header(self):
        ## lazy load asa this might not be use in many transformers
        import os
        from IPython.utils import path
        import io
        from pygments.formatters import HtmlFormatter
        header = []
        static = os.path.join(path.get_ipython_package_dir(),
            'frontend', 'html', 'notebook', 'static',
        )
        here = os.path.split(os.path.realpath(__file__))[0]
        css = os.path.join(static, 'css')
        for sheet in [
            # do we need jquery and prettify?
            # os.path.join(static, 'jquery', 'css', 'themes', 'base',
            # 'jquery-ui.min.css'),
            # os.path.join(static, 'prettify', 'prettify.css'),
            os.path.join(css, 'boilerplate.css'),
            os.path.join(css, 'fbm.css'),
            os.path.join(css, 'notebook.css'),
            os.path.join(css, 'renderedhtml.css'),
            os.path.join(css, 'style.min.css'),
        ]:
            try:
                with io.open(sheet, encoding='utf-8') as f:
                    s = f.read()
                    header.append(s)
            except IOError:
                # new version of ipython with style.min.css, pass
                pass

        pygments_css = HtmlFormatter().get_style_defs('.highlight')
        header.append(pygments_css)
        self.header = header

