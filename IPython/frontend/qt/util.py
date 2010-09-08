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
    """ A metaclass that inherits from the metaclasses of HasTraits and QObject.

    Using this metaclass allows a class to inherit from both HasTraits and
    QObject. See QtKernelManager for an example.
    """
    pass

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------

def get_font(family, fallback=None):
    """Return a font of the requested family, using fallback as alternative.

    If a fallback is provided, it is used in case the requested family isn't
    found.  If no fallback is given, no alternative is chosen and Qt's internal
    algorithms may automatically choose a fallback font.

    Parameters
    ----------
    family : str
      A font name.
    fallback : str
      A font name.

    Returns
    -------
    font : QFont object
    """
    font = QtGui.QFont(family)
    # Check whether we got what we wanted using QFontInfo, since exactMatch()
    # is overly strict and returns false in too many cases.
    font_info = QtGui.QFontInfo(font)
    if fallback is not None and font_info.family() != family:
        font = QtGui.QFont(fallback)
    return font
