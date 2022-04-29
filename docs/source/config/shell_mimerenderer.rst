
.. _shell_mimerenderer:


Mime Renderer Extensions
========================

Like it's cousins, Jupyter Notebooks and JupyterLab, Terminal IPython can be
thought to render a number of mimetypes in the shell. This can be used to either
display inline images if your terminal emulator supports it; or open some
display results with external file viewers.

Registering new mimetype handlers can so far only be done by extensions and
requires 4 steps:

   - Define a callable that takes 2 parameters:``data`` and ``metadata``; return
     value of the callable is so far ignored. This callable is responsible for
     "displaying" the given mimetype. Which can be sending the right escape
     sequences and bytes to the current terminal; or open an external program. -
   - Appending the right mimetype to ``ipython.display_formatter.active_types``
     for IPython to know it should not ignore those mimetypes.
   - Enabling the given mimetype: ``ipython.display_formatter.formatters[mime].enabled = True``
   - Registering above callable with mimetype handler:
     ``ipython.mime_renderers[mime] = handler``


Here is a complete IPython extension to display images inline and convert math
to png, before displaying it inline for iterm2 on macOS ::


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

This example only work for iterm2 on macOS and skip error handling for brevity.
One could also invoke an external viewer with ``subprocess.run()`` and a
temporary file, which is left as an exercise.
