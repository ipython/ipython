# Standard libary imports.
from base64 import decodestring
import os
import re

# System libary imports.
from IPython.external.qt import QtCore, QtGui

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

    #---------------------------------------------------------------------------
    # 'object' interface
    #---------------------------------------------------------------------------

    def __init__(self, *args, **kw):
        """ Create a RichIPythonWidget.
        """
        kw['kind'] = 'rich'
        super(RichIPythonWidget, self).__init__(*args, **kw)

        # Configure the ConsoleWidget HTML exporter for our formats.
        self._html_exporter.image_tag = self._get_image_tag

        # Dictionary for resolving document resource names to SVG data.
        self._name_to_svg_map = {}

    #---------------------------------------------------------------------------
    # 'ConsoleWidget' protected interface
    #---------------------------------------------------------------------------

    def _context_menu_make(self, pos):
        """ Reimplemented to return a custom context menu for images.
        """
        format = self._control.cursorForPosition(pos).charFormat()
        name = format.stringProperty(QtGui.QTextFormat.ImageName)
        if name:
            menu = QtGui.QMenu()

            menu.addAction('Copy Image', lambda: self._copy_image(name))
            menu.addAction('Save Image As...', lambda: self._save_image(name))
            menu.addSeparator()

            svg = self._name_to_svg_map.get(name, None)
            if svg is not None:
                menu.addSeparator()
                menu.addAction('Copy SVG', lambda: svg_to_clipboard(svg))
                menu.addAction('Save SVG As...',
                               lambda: save_svg(svg, self._control))
        else:
            menu = super(RichIPythonWidget, self)._context_menu_make(pos)
        return menu

    #---------------------------------------------------------------------------
    # 'BaseFrontendMixin' abstract interface
    #---------------------------------------------------------------------------

    def _handle_pyout(self, msg):
        """ Overridden to handle rich data types, like SVG.
        """
        if not self._hidden and self._is_from_this_session(msg):
            content = msg['content']
            prompt_number = content['execution_count']
            data = content['data']
            if data.has_key('image/svg+xml'):
                self.log.debug("pyout: %s", msg.get('content', ''))
                self._append_plain_text(self.output_sep, True)
                self._append_html(self._make_out_prompt(prompt_number), True)
                self._append_svg(data['image/svg+xml'], True)
                self._append_html(self.output_sep2, True)
            elif data.has_key('image/png'):
                self.log.debug("pyout: %s", msg.get('content', ''))
                self._append_plain_text(self.output_sep, True)
                self._append_html(self._make_out_prompt(prompt_number), True)
                # This helps the output to look nice.
                self._append_plain_text('\n', True)
                self._append_png(decodestring(data['image/png'].encode('ascii')), True)
                self._append_html(self.output_sep2, True)
            else:
                # Default back to the plain text representation.
                return super(RichIPythonWidget, self)._handle_pyout(msg)

    def _handle_display_data(self, msg):
        """ Overridden to handle rich data types, like SVG.
        """
        if not self._hidden and self._is_from_this_session(msg):
            source = msg['content']['source']
            data = msg['content']['data']
            metadata = msg['content']['metadata']
            # Try to use the svg or html representations.
            # FIXME: Is this the right ordering of things to try?
            if data.has_key('image/svg+xml'):
                self.log.debug("display: %s", msg.get('content', ''))
                svg = data['image/svg+xml']
                self._append_svg(svg, True)
            elif data.has_key('image/png'):
                self.log.debug("display: %s", msg.get('content', ''))
                # PNG data is base64 encoded as it passes over the network
                # in a JSON structure so we decode it.
                png = decodestring(data['image/png'].encode('ascii'))
                self._append_png(png, True)
            else:
                # Default back to the plain text representation.
                return super(RichIPythonWidget, self)._handle_display_data(msg)

    #---------------------------------------------------------------------------
    # 'RichIPythonWidget' protected interface
    #---------------------------------------------------------------------------

    def _append_png(self, png, before_prompt=False):
        """ Append raw PNG data to the widget.
        """
        self._append_custom(self._insert_png, png, before_prompt)

    def _append_svg(self, svg, before_prompt=False):
        """ Append raw SVG data to the widget.
        """
        self._append_custom(self._insert_svg, svg, before_prompt)

    def _add_image(self, image):
        """ Adds the specified QImage to the document and returns a
            QTextImageFormat that references it.
        """
        document = self._control.document()
        name = str(image.cacheKey())
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
        image = document.resource(QtGui.QTextDocument.ImageResource,
                                  QtCore.QUrl(name))
        return image

    def _get_image_tag(self, match, path = None, format = "png"):
        """ Return (X)HTML mark-up for the image-tag given by match.

        Parameters
        ----------
        match : re.SRE_Match
            A match to an HTML image tag as exported by Qt, with
            match.group("Name") containing the matched image ID.

        path : string|None, optional [default None]
            If not None, specifies a path to which supporting files may be
            written (e.g., for linked images).  If None, all images are to be
            included inline.

        format : "png"|"svg", optional [default "png"]
            Format for returned or referenced images.
        """
        if format == "png":
            try:
                image = self._get_image(match.group("name"))
            except KeyError:
                return "<b>Couldn't find image %s</b>" % match.group("name")

            if path is not None:
                if not os.path.exists(path):
                    os.mkdir(path)
                relpath = os.path.basename(path)
                if image.save("%s/qt_img%s.png" % (path,match.group("name")),
                              "PNG"):
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

        elif format == "svg":
            try:
                svg = str(self._name_to_svg_map[match.group("name")])
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

    def _insert_png(self, cursor, png):
        """ Insert raw PNG data into the widget.
        """
        try:
            image = QtGui.QImage()
            image.loadFromData(png, 'PNG')
        except ValueError:
            self._insert_plain_text(cursor, 'Received invalid PNG data.')
        else:
            format = self._add_image(image)
            cursor.insertBlock()
            cursor.insertImage(format)
            cursor.insertBlock()

    def _insert_svg(self, cursor, svg):
        """ Insert raw SVG data into the widet.
        """
        try:
            image = svg_to_image(svg)
        except ValueError:
            self._insert_plain_text(cursor, 'Received invalid SVG data.')
        else:
            format = self._add_image(image)
            self._name_to_svg_map[format.name()] = svg
            cursor.insertBlock()
            cursor.insertImage(format)
            cursor.insertBlock()

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
