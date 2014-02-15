# Use CoffeeScript in IPython notebook. CoffeeScript is executed in
# the global (window) context to make variables accessible across
# cells.
#
# Example:
#
# > %%coffee
# > console.log "Hello from CoffeeScript!"
#
# Note: this needs various patches to IPython, for example in
# IPython/html/static/notebook/js/outputarea.js and the CoffeeScript
# compiler in IPython/html/static/coffee-script.js.
#
# CoffeeScript execution works similarly to the built-in javascript
# cell magic.  The cell contents is sent back from the kernel for
# display with a MIME type of 'application/coffeescript'. The MIME
# type is recognized and executed on the notebook client in
# IPython.OutputArea.append_mime_type.

from IPython.core.magic import Magics, magics_class,  cell_magic
from IPython.core.displaypub import publish_display_data

@magics_class
class CoffeeScript(Magics):

    @cell_magic
    def coffee(self, line, cell):
        """Send the cell contents back to the client with MIME type application/coffeescript.
        """
        publish_display_data('CoffeeScriptMagic',
            {
                'application/coffeescript': cell
            })

def load_ipython_extension(ip):
    cs = CoffeeScript(ip)
    ip.register_magics(cs)
