#-----------------------------------------------------------------------------
# Copyright (c) 2010, IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

# Standard libary imports.
from base64 import decodestring
import os
import re

# System libary imports.
from IPython.external.qt import QtCore, QtGui

# Local imports
from IPython.utils.traitlets import Bool
from IPython.qt.svg import save_svg, svg_to_clipboard, svg_to_image
from .ipython_widget import IPythonWidget


class RichIPythonWidget(IPythonWidget):
    """ An IPythonWidget that supports rich text, including lists, images, and
        tables. Note that raw performance will be reduced compared to the plain
        text version.
    """

    # RichIPythonWidget protected class variables.
    _payload_source_plot = 'IPython.kernel.zmq.pylab.backend_payload.add_plot_payload'
    _jpg_supported = Bool(False)

    # Used to determine whether a given html export attempt has already
    # displayed a warning about being unable to convert a png to svg.
    _svg_warning_displayed = False

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

        # Do we support jpg ?
        # it seems that sometime jpg support is a plugin of QT, so try to assume
        # it is not always supported.
        _supported_format = map(str, QtGui.QImageReader.supportedImageFormats())
        self._jpg_supported = 'jpeg' in _supported_format


    #---------------------------------------------------------------------------
    # 'ConsoleWidget' public interface overides
    #---------------------------------------------------------------------------

    def export_html(self):
        """ Shows a dialog to export HTML/XML in various formats.

        Overridden in order to reset the _svg_warning_displayed flag prior
        to the export running.
        """
        self._svg_warning_displayed = False
        super(RichIPythonWidget, self).export_html()


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
    def _pre_image_append(self, msg, prompt_number):
        """ Append the Out[] prompt  and make the output nicer

        Shared code for some the following if statement
        """
        self.log.debug("pyout: %s", msg.get('content', ''))
        self._append_plain_text(self.output_sep, True)
        self._append_html(self._make_out_prompt(prompt_number), True)
        self._append_plain_text('\n', True)

    def _handle_pyout(self, msg):
        """ Overridden to handle rich data types, like SVG.
        """
        if not self._hidden and self._is_from_this_session(msg):
            self.flush_clearoutput()
            content = msg['content']
            prompt_number = content.get('execution_count', 0)
            data = content['data']
            metadata = msg['content']['metadata']
            if 'image/svg+xml' in data:
                self._pre_image_append(msg, prompt_number)
                self._append_svg(data['image/svg+xml'], True)
                self._append_html(self.output_sep2, True)
            elif 'image/png' in data:
                self._pre_image_append(msg, prompt_number)
                png = decodestring(data['image/png'].encode('ascii'))
                self._append_png(png, True, metadata=metadata.get('image/png', None))
                self._append_html(self.output_sep2, True)
            elif 'image/jpeg' in data and self._jpg_supported:
                self._pre_image_append(msg, prompt_number)
                jpg = decodestring(data['image/jpeg'].encode('ascii'))
                self._append_jpg(jpg, True, metadata=metadata.get('image/jpeg', None))
                self._append_html(self.output_sep2, True)
            else:
                # Default back to the plain text representation.
                return super(RichIPythonWidget, self)._handle_pyout(msg)

    def _handle_display_data(self, msg):
        """ Overridden to handle rich data types, like SVG.
        """
        if not self._hidden and self._is_from_this_session(msg):
            self.flush_clearoutput()
            source = msg['content']['source']
            data = msg['content']['data']
            metadata = msg['content']['metadata']
            # Try to use the svg or html representations.
            # FIXME: Is this the right ordering of things to try?
            if 'image/svg+xml' in data:
                self.log.debug("display: %s", msg.get('content', ''))
                svg = data['image/svg+xml']
                self._append_svg(svg, True)
            elif 'image/png' in data:
                self.log.debug("display: %s", msg.get('content', ''))
                # PNG data is base64 encoded as it passes over the network
                # in a JSON structure so we decode it.
                png = decodestring(data['image/png'].encode('ascii'))
                self._append_png(png, True, metadata=metadata.get('image/png', None))
            elif 'image/jpeg' in data and self._jpg_supported:
                self.log.debug("display: %s", msg.get('content', ''))
                jpg = decodestring(data['image/jpeg'].encode('ascii'))
                self._append_jpg(jpg, True, metadata=metadata.get('image/jpeg', None))
            else:
                # Default back to the plain text representation.
                return super(RichIPythonWidget, self)._handle_display_data(msg)

    #---------------------------------------------------------------------------
    # 'RichIPythonWidget' protected interface
    #---------------------------------------------------------------------------

    def _append_jpg(self, jpg, before_prompt=False, metadata=None):
        """ Append raw JPG data to the widget."""
        self._append_custom(self._insert_jpg, jpg, before_prompt, metadata=metadata)

    def _append_png(self, png, before_prompt=False, metadata=None):
        """ Append raw PNG data to the widget.
        """
        self._append_custom(self._insert_png, png, before_prompt, metadata=metadata)

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

        format : "png"|"svg"|"jpg", optional [default "png"]
            Format for returned or referenced images.
        """
        if format in ("png","jpg"):
            try:
                image = self._get_image(match.group("name"))
            except KeyError:
                return "<b>Couldn't find image %s</b>" % match.group("name")

            if path is not None:
                if not os.path.exists(path):
                    os.mkdir(path)
                relpath = os.path.basename(path)
                if image.save("%s/qt_img%s.%s" % (path, match.group("name"), format),
                              "PNG"):
                    return '<img src="%s/qt_img%s.%s">' % (relpath,
                                                            match.group("name"),format)
                else:
                    return "<b>Couldn't save image!</b>"
            else:
                ba = QtCore.QByteArray()
                buffer_ = QtCore.QBuffer(ba)
                buffer_.open(QtCore.QIODevice.WriteOnly)
                image.save(buffer_, format.upper())
                buffer_.close()
                return '<img src="data:image/%s;base64,\n%s\n" />' % (
                    format,re.sub(r'(.{60})',r'\1\n',str(ba.toBase64())))

        elif format == "svg":
            try:
                svg = str(self._name_to_svg_map[match.group("name")])
            except KeyError:
                if not self._svg_warning_displayed:
                    QtGui.QMessageBox.warning(self, 'Error converting PNG to SVG.',
                        'Cannot convert PNG images to SVG, export with PNG figures instead. '
                        'If you want to export matplotlib figures as SVG, add '
                        'to your ipython config:\n\n'
                        '\tc.InlineBackend.figure_format = \'svg\'\n\n'
                        'And regenerate the figures.',
                                              QtGui.QMessageBox.Ok)
                    self._svg_warning_displayed = True
                return ("<b>Cannot convert  PNG images to SVG.</b>  "
                        "You must export this session with PNG images. "
                        "If you want to export matplotlib figures as SVG, add to your config "
                        "<span>c.InlineBackend.figure_format = 'svg'</span> "
                        "and regenerate the figures.")

            # Not currently checking path, because it's tricky to find a
            # cross-browser way to embed external SVG images (e.g., via
            # object or embed tags).

            # Chop stand-alone header from matplotlib SVG
            offset = svg.find("<svg")
            assert(offset > -1)

            return svg[offset:]

        else:
            return '<b>Unrecognized image format</b>'

    def _insert_jpg(self, cursor, jpg, metadata=None):
        """ Insert raw PNG data into the widget."""
        self._insert_img(cursor, jpg, 'jpg', metadata=metadata)

    def _insert_png(self, cursor, png, metadata=None):
        """ Insert raw PNG data into the widget.
        """
        self._insert_img(cursor, png, 'png', metadata=metadata)

    def _insert_img(self, cursor, img, fmt, metadata=None):
        """ insert a raw image, jpg or png """
        if metadata:
            width = metadata.get('width', None)
            height = metadata.get('height', None)
        else:
            width = height = None
        try:
            image = QtGui.QImage()
            image.loadFromData(img, fmt.upper())
            if width and height:
                image = image.scaled(width, height, transformMode=QtCore.Qt.SmoothTransformation)
            elif width and not height:
                image = image.scaledToWidth(width, transformMode=QtCore.Qt.SmoothTransformation)
            elif height and not width:
                image = image.scaledToHeight(height, transformMode=QtCore.Qt.SmoothTransformation)
        except ValueError:
            self._insert_plain_text(cursor, 'Received invalid %s data.'%fmt)
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
