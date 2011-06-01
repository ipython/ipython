""" Defines utility functions for working with SVG documents in Qt.
"""

# System library imports.
from IPython.external.qt import QtCore, QtGui, QtSvg


def save_svg(string, parent=None):
    """ Prompts the user to save an SVG document to disk.

    Parameters:
    -----------
    string : basestring
        A Python string containing a SVG document.

    parent : QWidget, optional
        The parent to use for the file dialog.

    Returns:
    --------
    The name of the file to which the document was saved, or None if the save
    was cancelled.
    """
    if isinstance(string, unicode):
        string = string.encode('utf-8')

    dialog = QtGui.QFileDialog(parent, 'Save SVG Document')
    dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
    dialog.setDefaultSuffix('svg')
    dialog.setNameFilter('SVG document (*.svg)')
    if dialog.exec_():
        filename = dialog.selectedFiles()[0]
        f = open(filename, 'w')
        try:
            f.write(string)
        finally:
            f.close()
        return filename
    return None

def svg_to_clipboard(string):
    """ Copy a SVG document to the clipboard.

    Parameters:
    -----------
    string : basestring
        A Python string containing a SVG document.
    """
    if isinstance(string, unicode):
        string = string.encode('utf-8')

    mime_data = QtCore.QMimeData()
    mime_data.setData('image/svg+xml', string)
    QtGui.QApplication.clipboard().setMimeData(mime_data)
        
def svg_to_image(string, size=None):
    """ Convert a SVG document to a QImage.

    Parameters:
    -----------
    string : basestring
        A Python string containing a SVG document.

    size : QSize, optional
        The size of the image that is produced. If not specified, the SVG
        document's default size is used.
    
    Raises:
    -------
    ValueError
        If an invalid SVG string is provided.

    Returns:
    --------
    A QImage of format QImage.Format_ARGB32.
    """
    if isinstance(string, unicode):
        string = string.encode('utf-8')

    renderer = QtSvg.QSvgRenderer(QtCore.QByteArray(string))
    if not renderer.isValid():
        raise ValueError('Invalid SVG data.')

    if size is None:
        size = renderer.defaultSize()
    image = QtGui.QImage(size, QtGui.QImage.Format_ARGB32)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    return image
