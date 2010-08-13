# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.frontend.qt.util import image_from_svg
from ipython_widget import IPythonWidget


class RichIPythonWidget(IPythonWidget):
    """ An IPythonWidget that supports rich text, including lists, images, and
        tables. Note that raw performance will be reduced compared to the plain
        text version.
    """

    #---------------------------------------------------------------------------
    # 'QObject' interface
    #---------------------------------------------------------------------------

    def __init__(self, parent=None):
        """ Create a RichIPythonWidget.
        """
        super(RichIPythonWidget, self).__init__(kind='rich', parent=parent)
    
    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _handle_execute_payload(self, payload):
        """ Reimplemented to handle pylab plot payloads.
        """
        plot_payload = payload.get('plot', None)
        if plot_payload and plot_payload['format'] == 'svg':
            try:
                image = image_from_svg(plot_payload['data'])
            except ValueError:
                self._append_plain_text('Received invalid plot data.')
            else:
                cursor = self._get_end_cursor()
                cursor.insertBlock()
                cursor.insertImage(image)
                cursor.insertBlock()
        else:
            super(RichIPythonWidget, self)._handle_execute_payload(payload)
