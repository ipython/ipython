import os

# System library imports
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.frontend.qt.svg import save_svg, svg_to_clipboard, svg_to_image
from ipython_widget import IPythonWidget


class RichIPythonWidget(IPythonWidget):
    """ An IPythonWidget that supports rich text, including lists, images, and
        tables. Note that raw performance will be reduced compared to the plain
        text version.
    """

    # Protected class variables.
    _svg_text_format_property = 1

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        """ Create a RichIPythonWidget.
        """
        kw['kind'] = 'rich'
        super(RichIPythonWidget, self).__init__(*args, **kw)

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _show_context_menu(self, pos):
        """ Reimplemented to show a custom context menu for images.
        """
        format = self._control.cursorForPosition(pos).charFormat()
        name = format.stringProperty(QtGui.QTextFormat.ImageName)
        if name.isEmpty():
            super(RichIPythonWidget, self)._show_context_menu(pos)
        else:
            menu = QtGui.QMenu()

            menu.addAction('Copy Image', lambda: self._copy_image(name))
            menu.addAction('Save Image As...', lambda: self._save_image(name))
            menu.addSeparator()

            svg = format.stringProperty(self._svg_text_format_property)
            if not svg.isEmpty():
                menu.addSeparator()
                menu.addAction('Copy SVG', lambda: svg_to_clipboard(svg))
                menu.addAction('Save SVG As...', 
                               lambda: save_svg(svg, self._control))
                
            menu.exec_(self._control.mapToGlobal(pos))
    
    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _process_execute_ok(self, msg):
        """ Reimplemented to handle matplotlib plot payloads.
        """
        payload = msg['content']['payload']
        for item in payload:
            if item['source'] == 'IPython.zmq.pylab.backend_payload.add_plot_payload':
                if item['format'] == 'svg':
                    svg = item['data']
                    try:
                        image = svg_to_image(svg)
                    except ValueError:
                        self._append_plain_text('Received invalid plot data.')
                    else:
                        format = self._add_image(image)
                        format.setProperty(self._svg_text_format_property, svg)
                        cursor = self._get_end_cursor()
                        cursor.insertBlock()
                        cursor.insertImage(format)
                        cursor.insertBlock()
                else:
                    # Add other plot formats here!
                    pass
            elif item['source'] == 'IPython.zmq.zmqshell.ZMQInteractiveShell.edit_magic':
                # TODO: I have implmented the logic for TextMate on the Mac.
                # But, we need to allow payload handlers on the non-rich
                # text IPython widget as well. Furthermore, we should probably
                # move these handlers to separate methods. But, we need to
                # be very careful to process the payload list in order. Thus,
                # we will probably need a _handle_payload method of the 
                # base class that dispatches to the separate handler methods
                # for each payload source. If a particular subclass doesn't 
                # have a handler for a payload source, it should at least
                # print a nice message.
                filename = item['filename']
                line_number = item['line_number']
                if line_number is None:
                    cmd = 'mate %s' % filename
                else:
                    cmd = 'mate -l %s %s' % (line_number, filename)
                os.system(cmd)
            else:
                # Add other payload types here!
                pass
        else:
            super(RichIPythonWidget, self)._process_execute_ok(msg)

    #---------------------------------------------------------------------------
    # 'RichIPythonWidget' protected interface
    #---------------------------------------------------------------------------

    def _add_image(self, image):
        """ Adds the specified QImage to the document and returns a
            QTextImageFormat that references it.
        """
        document = self._control.document()
        name = QtCore.QString.number(image.cacheKey())
        document.addResource(QtGui.QTextDocument.ImageResource,
                             QtCore.QUrl(name), image)
        format = QtGui.QTextImageFormat()
        format.setName(name)
        return format

    def _copy_image(self, name):
        """ Copies the ImageResource with 'name' to the clipboard.
        """
        image = self._get_image(name)
        QtGui.QApplication.clipboard().setImage(image)

    def _get_image(self, name):
        """ Returns the QImage stored as the ImageResource with 'name'.
        """
        document = self._control.document()
        variant = document.resource(QtGui.QTextDocument.ImageResource,
                                    QtCore.QUrl(name))
        return variant.toPyObject()

    def _save_image(self, name, format='PNG'):
        """ Shows a save dialog for the ImageResource with 'name'.
        """
        dialog = QtGui.QFileDialog(self._control, 'Save Image')
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        dialog.setDefaultSuffix(format.lower())
        dialog.setNameFilter('%s file (*.%s)' % (format, format.lower()))
        if dialog.exec_():
            filename = dialog.selectedFiles()[0]
            image = self._get_image(name)
            image.save(filename, format)
