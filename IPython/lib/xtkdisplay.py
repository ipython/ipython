"""Display classes for the XTK JavaScript library.

The XTK JavaScript library uses WebGL to render 3D visualizations. It can
generate those visualizations based a range of standard 3D data files types,
including .vtk and .stl.  This module makes it possible to render these
visualizations in the IPython Notebook.

A simple example would be::

    from IPython.lib.xtkdisplay import Mesh
    Mesh('http://x.babymri.org/?skull.vtk', opacity=0.5, magicmode=True)

Authors:

* Brian Granger
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2012  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os

from IPython.core.display import Javascript

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


code = """
    container.show();
    var id = 'xtkwidget_' + utils.uuid();
    var xtkdiv = $('<div/>').attr('id',id);
    xtkdiv.css('background-color','%s').width(%i).height(%i);
    element.append(xtkdiv);
    var r = new X.renderer3D();
    r.container = id;
    r.init();
    var m = new X.mesh();
    m.file = "%s";
    m.magicmode = %s;
    m.opacity = %f;
    r.add(m);
    r.render();
"""

class Mesh(object):
    """Display an XTK mesh object using a URL."""
    
    def __init__(self, url, width=400, height=300, magicmode=False, opacity=1.0, bgcolor='#000'):
        """Create an XTK mesh from a URL.
        
        Parameters
        ==========
        url : str
            The URL to the data files to render. This can be an absolute URL or one that is
            relative to the notebook server ('files/mymesh.vtk').
        width : int
            The width in pixels of the XTK widget.
        height : int
            The height in pixels of the XTK widget.
        magicmode : bool
            Enable magicmode, which colors points based on their positions.
        opacity : float
            The mesh's opacity in the range 0.0 to 1.0.
        bgcolor : str
            The XTK widget's background color.
        """
        self.url = url
        self.width = width
        self.height = height
        self.magicmode = 'true' if magicmode else 'false'
        self.opacity = opacity
        self.bgcolor = bgcolor

    def _repr_javascript_(self):
        js = code % (self.bgcolor, self.width, self.height, self.url, self.magicmode, self.opacity)
        js = Javascript(js, lib='http://get.goXTK.com/xtk_edge.js')
        return js._repr_javascript_()

