""" Defines miscellaneous Qt-related helper classes and functions.
"""

# System library imports.
from PyQt4 import QtCore, QtGui

# IPython imports.
from IPython.utils.traitlets import HasTraits

#-----------------------------------------------------------------------------
# Metaclasses
#-----------------------------------------------------------------------------

MetaHasTraits = type(HasTraits)
MetaQObject = type(QtCore.QObject)

# You can switch the order of the parents here and it doesn't seem to matter.
class MetaQObjectHasTraits(MetaQObject, MetaHasTraits):
    """ A metaclass that inherits from the metaclasses of both HasTraits and
        QObject. 

        Using this metaclass allows a class to inherit from both HasTraits and
        QObject. See QtKernelManager for an example.
    """
    pass

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
        
def image_from_svg(string, size=None):
    """ Convert a SVG document to a QImage.

    Parameters:
    -----------
    string : str
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
    from PyQt4 import QtSvg

    bytes = QtCore.QByteArray.fromRawData(string) # shallow copy
    renderer = QtSvg.QSvgRenderer(bytes)
    if not renderer.isValid():
        raise ValueError('Invalid SVG data.')

    if size is None:
        size = renderer.defaultSize()
    image = QtGui.QImage(size, QtGui.QImage.Format_ARGB32)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    return image
