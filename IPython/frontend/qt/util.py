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
    """ Convert a string containing SVG data into a QImage.

    Parameters:
    -----------
    string : str
        A Python string containing the SVG data.

    size : QSize or None [default None]
        The size of the image that is produced. If not specified, the SVG data's
        default size is used.
    
    Raises:
    -------
    ValueError
        If an invalid SVG string is provided.

    Returns:
    --------
    A QImage with format QImage.Format_ARGB32_Premultiplied.
    """
    from PyQt4 import QtSvg

    bytes = QtCore.QByteArray(string)
    renderer = QtSvg.QSvgRenderer(bytes)
    if not renderer.isValid():
        raise ValueError('Invalid SVG data.')

    if size is None:
        size = renderer.defaultSize()
    image = QtGui.QImage(size, QtGui.QImage.Format_ARGB32_Premultiplied)
    painter = QtGui.QPainter(image)
    renderer.render(painter)
    return image
