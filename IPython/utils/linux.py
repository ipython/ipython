# -*- coding: utf-8 -*-

from pygments.style import Style

class LinuxStyle(Style):
    """
    The default style (inspired by Emacs 22).
    """

    background_color = "#f8f8f8"
    default_style = ""

    style = defaultdict(lambda:'bold #BB0000', {'':''})
