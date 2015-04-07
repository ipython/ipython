# encoding: utf-8
"""
Trait types for html widgets.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import re
from IPython.utils import traitlets

from . import eventful

_color_names = ['aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise', 'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow', 'honeydew', 'hotpink', 'indianred ', 'indigo ', 'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow', 'lightgray', 'lightgreen', 'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue', 'lightslategray', 'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine', 'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue', 'mediumspringgreen', 'mediumturquoise', 'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum', 'powderblue', 'purple', 'rebeccapurple', 'red', 'rosybrown', 'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke', 'yellow', 'yellowgreen'] 
_color_re = re.compile(r'#[a-fA-F0-9]{3}(?:[a-fA-F0-9]{3})?$')


class Color(traitlets.Unicode):
    """A string holding a valid HTML color such as 'blue', '#060482', '#A80'"""
 
    info_text = 'a valid HTML color'

    def validate(self, obj, value):
        if value.lower() in _color_names or _color_re.match(value):
            return value
        self.error(obj, value)


class EventfulDict(traitlets.Instance):
    """An instance of an EventfulDict."""

    def __init__(self, default_value={}, **metadata):
        """Create a EventfulDict trait type from a dict.

        The default value is created by doing
        ``eventful.EvenfulDict(default_value)``, which creates a copy of the
        ``default_value``.
        """
        if default_value is None:
            args = None
        elif isinstance(default_value, dict):
            args = (default_value,)
        elif isinstance(default_value, SequenceTypes):
            args = (default_value,)
        else:
            raise TypeError('default value of EventfulDict was %s' % default_value)

        super(EventfulDict, self).__init__(klass=eventful.EventfulDict, args=args,
                                           **metadata)


class EventfulList(traitlets.Instance):
    """An instance of an EventfulList."""

    def __init__(self, default_value=None, **metadata):
        """Create a EventfulList trait type from a dict.

        The default value is created by doing 
        ``eventful.EvenfulList(default_value)``, which creates a copy of the 
        ``default_value``.
        """
        if default_value is None:
            args = ((),)
        else:
            args = (default_value,)

        super(EventfulList, self).__init__(klass=eventful.EventfulList, args=args,
                                           **metadata)


