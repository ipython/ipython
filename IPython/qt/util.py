""" Defines miscellaneous Qt-related helper classes and functions.
"""

# Standard library imports.
import inspect

# System library imports.
from IPython.external.qt import QtCore, QtGui

# IPython imports.
from IPython.utils.py3compat import iteritems
from IPython.utils.traitlets import HasTraits, TraitType

#-----------------------------------------------------------------------------
# Metaclasses
#-----------------------------------------------------------------------------

MetaHasTraits = type(HasTraits)
MetaQObject = type(QtCore.QObject)

class MetaQObjectHasTraits(MetaQObject, MetaHasTraits):
    """ A metaclass that inherits from the metaclasses of HasTraits and QObject.

    Using this metaclass allows a class to inherit from both HasTraits and
    QObject. Using SuperQObject instead of QObject is highly recommended. See
    QtKernelManager for an example.
    """
    def __new__(mcls, name, bases, classdict):
        # FIXME: this duplicates the code from MetaHasTraits.
        # I don't think a super() call will help me here.
        for k,v in iteritems(classdict):
            if isinstance(v, TraitType):
                v.name = k
            elif inspect.isclass(v):
                if issubclass(v, TraitType):
                    vinst = v()
                    vinst.name = k
                    classdict[k] = vinst
        cls = MetaQObject.__new__(mcls, name, bases, classdict)
        return cls

    def __init__(mcls, name, bases, classdict):
        # Note: super() did not work, so we explicitly call these.
        MetaQObject.__init__(mcls, name, bases, classdict)
        MetaHasTraits.__init__(mcls, name, bases, classdict)

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------

class SuperQObject(QtCore.QObject):
    """ Permits the use of super() in class hierarchies that contain QObject.

    Unlike QObject, SuperQObject does not accept a QObject parent. If it did,
    super could not be emulated properly (all other classes in the heierarchy
    would have to accept the parent argument--they don't, of course, because
    they don't inherit QObject.)

    This class is primarily useful for attaching signals to existing non-Qt
    classes. See QtKernelManagerMixin for an example.
    """

    def __new__(cls, *args, **kw):
        # We initialize QObject as early as possible. Without this, Qt complains
        # if SuperQObject is not the first class in the super class list.
        inst = QtCore.QObject.__new__(cls)
        QtCore.QObject.__init__(inst)
        return inst

    def __init__(self, *args, **kw):
        # Emulate super by calling the next method in the MRO, if there is one.
        mro = self.__class__.mro()
        for qt_class in QtCore.QObject.mro():
            mro.remove(qt_class)
        next_index = mro.index(SuperQObject) + 1
        if next_index < len(mro):
            mro[next_index].__init__(self, *args, **kw)

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
