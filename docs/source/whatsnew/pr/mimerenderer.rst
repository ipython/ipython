Arbitrary Mimetypes Handing in Terminal
=======================================

When using IPython terminal it is now possible to register function to handle
arbitrary mimetypes (``TerminalInteractiveShell.mime_renderers`` ``Dict``
configurable). While rendering non-text based representation was possible in
many jupyter frontend; it was not possible in terminal IPython, as usually
terminal are limited to displaying text. As many terminal these days provide
escape sequences to display non-text; bringing this loved feature to IPython CLI
made a lot of sens. This functionality will not only allow inline images; but
allow opening of external program; for example ``fmplayer`` to "display" sound
files.

Here is a complete IPython tension to display images inline and convert math to
png, before displaying it inline ::


    from base64 import encodebytes
    from IPython.lib.latextools import latex_to_png


    def mathcat(data, meta):
        png = latex_to_png(f'$${data}$$'.replace('\displaystyle', '').replace('$$$', '$$'))
        imcat(png, meta)

    IMAGE_CODE = '\033]1337;File=name=name;inline=true;:{}\a'

    def imcat(image_data, metadata):
        try:
            print(IMAGE_CODE.format(encodebytes(image_data).decode()))
        # bug workaround
        except:
            print(IMAGE_CODE.format(image_data))

    def register_mimerenderer(ipython, mime, handler):
        ipython.display_formatter.active_types.append(mime)
        ipython.display_formatter.formatters[mime].enabled = True
        ipython.mime_renderers[mime] = handler

    def load_ipython_extension(ipython):
        register_mimerenderer(ipython, 'image/png', imcat)
        register_mimerenderer(ipython, 'image/jpeg', imcat)
        register_mimerenderer(ipython, 'text/latex', mathcat)

This example only work for iterm2 on mac os and skip error handling for brevity.
One could also invoke an external viewer with ``subporcess.run()`` and a
tempfile, which is left as an exercise.

So far only the hooks necessary for this are in place, but no default mime
renderers added; so inline images will only be available via extensions. We will
progressively enable these features by default in the next few releases, and
contribution is welcomed.



