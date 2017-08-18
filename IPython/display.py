"""Public API for display tools in IPython.

This module regroup all public API function and classes related to the rich
IPython display system. This allows you to create, manipulate and display rich
objects in various ways.

You can display rich representation of objects using  :func:`display`, update
the current output or clear it if supported with :func:`clear_output`, and
:func:`update_display`.

A number of convenience functions wrapping ``display(object, include=...)``
allows you to filter the representations of objects to show.

  - :func:`display_html`, :func:`display_javascript`, :func:`display_jpeg`,
    :func:`display_json`, :func:`display_latex`, :func:`display_markdown`,
    :func:`display_pdf`, :func:`display_png`, :func:`display_pretty`,
    :func:`display_svg`, ...

You will find a variety of objects providing rich representation for common use cases:

  - :class:`Audio`, :class:`DisplayHandle`, :class:`DisplayObject`,
    :class:`FileLink`, :class:`FileLinks`, :class:`GeoJSON`, :class:`HTML`,
    :class:`IFrame`, :class:`Image`, :class:`JSON`, :class:`Javascript`,
    :class:`Latex`, :class:`Markdown`, :class:`Math`, :class:`Pretty`,
    :class:`SVG`, :class:`ScribdDocument`, :class:`TextDisplayObject`,
    :class:`Video`, :class:`VimeoVideo`, :class:`YouTubeVideo`, ...

And a couple of lower level function to programmatically combine rich
representation and how they are send to frontends:
 
 - :any:`get_repr_mimebundle`, :func:`publish_display_data`


"""

#-----------------------------------------------------------------------------
#       Copyright (C) 2012 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from IPython.core.display import *
from IPython.lib.display import *

