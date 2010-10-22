# System library imports
import os
import re
from PyQt4 import QtCore, QtGui

# Local imports
from IPython.frontend.qt.svg import save_svg, svg_to_clipboard, svg_to_image
from ipython_widget import IPythonWidget


class RichIPythonWidget(IPythonWidget):
    """ An IPythonWidget that supports rich text, including lists, images, and
        tables. Note that raw performance will be reduced compared to the plain
        text version.
    """

    # RichIPythonWidget protected class variables.
    _payload_source_plot = 'IPython.zmq.pylab.backend_payload.add_plot_payload'
    _svg_text_format_property = 1

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        """ Create a RichIPythonWidget.
        """
        kw['kind'] = 'rich'
        super(RichIPythonWidget, self).__init__(*args, **kw)
        # Dictionary for resolving Qt names to images when
        # generating XHTML output
        self._name_to_svg = {}

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _context_menu_make(self, pos):
        """ Reimplemented to return a custom context menu for images.
        """
        format = self._control.cursorForPosition(pos).charFormat()
        name = format.stringProperty(QtGui.QTextFormat.ImageName)
        if name.isEmpty():
            menu = super(RichIPythonWidget, self)._context_menu_make(pos)
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
        return menu
    
    #---------------------------------------------------------------------------
    # 'FrontendWidget' protected interface
    #---------------------------------------------------------------------------

    def _process_execute_payload(self, item):
        """ Reimplemented to handle matplotlib plot payloads.
        """
        if item['source'] == self._payload_source_plot:
            if item['format'] == 'svg':
                svg = item['data']
                try:
                    image = svg_to_image(svg)
                except ValueError:
                    self._append_plain_text('Received invalid plot data.')
                else:
                    format = self._add_image(image)
                    self._name_to_svg[str(format.name())] = svg
                    format.setProperty(self._svg_text_format_property, svg)
                    cursor = self._get_end_cursor()
                    cursor.insertBlock()
                    cursor.insertImage(format)
                    cursor.insertBlock()
                return True
            else:
                # Add other plot formats here!
                return False
        else:
            return super(RichIPythonWidget, self)._process_execute_payload(item)

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

    def image_tag(self, match, path = None, format = "png"):
        """ Return (X)HTML mark-up for the image-tag given by match.

        Parameters
        ----------
        match : re.SRE_Match 
            A match to an HTML image tag as exported by Qt, with
            match.group("Name") containing the matched image ID.

        path : string|None, optional [default None]
            If not None, specifies a path to which supporting files
            may be written (e.g., for linked images).
            If None, all images are to be included inline.

        format : "png"|"svg", optional [default "png"]
            Format for returned or referenced images.

        Subclasses supporting image display should override this
        method.
        """

        if(format == "png"):
            try:
                image = self._get_image(match.group("name"))
            except KeyError:
                return "<b>Couldn't find image %s</b>" % match.group("name")

            if(path is not None):
                if not os.path.exists(path):
                    os.mkdir(path)
                relpath = os.path.basename(path)
                if(image.save("%s/qt_img%s.png" % (path,match.group("name")),
                              "PNG")):
                    return '<img src="%s/qt_img%s.png">' % (relpath,
                                                            match.group("name"))
                else:
                    return "<b>Couldn't save image!</b>"
            else:
                ba = QtCore.QByteArray()
                buffer_ = QtCore.QBuffer(ba)
                buffer_.open(QtCore.QIODevice.WriteOnly)
                image.save(buffer_, "PNG")
                buffer_.close()
                return '<img src="data:image/png;base64,\n%s\n" />' % (
                    re.sub(r'(.{60})',r'\1\n',str(ba.toBase64())))

        elif(format == "svg"):
            try:
                svg = str(self._name_to_svg[match.group("name")])
            except KeyError:
                return "<b>Couldn't find image %s</b>" % match.group("name")

            # Not currently checking path, because it's tricky to find a
            # cross-browser way to embed external SVG images (e.g., via
            # object or embed tags).

            # Chop stand-alone header from matplotlib SVG
            offset = svg.find("<svg")
            assert(offset > -1)
            
            return svg[offset:]

        else:
            return '<b>Unrecognized image format</b>'
        
