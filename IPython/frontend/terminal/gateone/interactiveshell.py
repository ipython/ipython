from ..console.interactiveshell import ZMQTerminalInteractiveShell
from IPython.utils.traitlets import List, Enum, Any
import base64

class GateOneInteractiveShell(ZMQTerminalInteractiveShell):
    image_handler = Enum(('gateone'), default_value='gateone',
                         config=True, help=
        """
        Handler for image type output.  This is useful, for example,
        when connecting to the kernel in which pylab inline backend is
        activated.  There are four handlers defined.  'PIL': Use
        Python Imaging Library to popup image; 'stream': Use an
        external program to show the image.  Image will be fed into
        the STDIN of the program.  You will need to configure
        `stream_image_handler`; 'tempfile': Use an external program to
        show the image.  Image will be saved in a temporally file and
        the program is called with the temporally file.  You will need
        to configure `tempfile_image_handler`; 'callable': You can set
        any Python callable which is called with the image data.  You
        will need to configure `callable_image_handler`.
        """
    )
    script_to_run = Any(config=True)
    
    def handle_image_gateone(self, data, mime):
        if mime not in ('image/png'):
            return
        img = base64.decodestring(data[mime].encode('ascii'))
        print(img)
        
    def init_callback(self):
        if self.script_to_run:
            self.run_cell('run %s' % self.script_to_run)

