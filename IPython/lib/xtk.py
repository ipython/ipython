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
import uuid

from IPython.display import Javascript, display

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------


def load_xtk():
    js = 'alert("XTK library loaded");'
    display(Javascript(js, lib='http://get.goXTK.com/xtk_edge.js'))


class Base(object):
    
    _xtk_name = 'base'

    def __init__(self):
        self.id = unicode(uuid.uuid4()).replace('-','')
        self.var = 'obj_' + self.id



_object_template = """
    var %s = new X.%s();
    %s.magicmode = %s;
    %s.opacity = %f;
    %s.color = [%f,%f,%f];
"""

class Object(Base):

    _xtk_name = 'object'

    def __init__(self, magicmode=False, opacity=1.0, color=(1.0,1.0,1.0)):
        super(Object, self).__init__()
        for value in (opacity,)+color:
            if not isinstance(value, float):
                raise TypeError('opacity and color values must be floats')
            if value > 1.0 or value < 0.0:
                raise ValueError('opacity and color values must be in the range [0.0,1.0]')
        self.magicmode = 'true' if magicmode else 'false'
        self.opacity = opacity
        self.color = color

    def generate_js_fragment(self):
        return _object_template % (self.var, self._xtk_name, self.var, self.magicmode,
            self.var, self.opacity, self.var, self.color[0], self.color[1], self.color[2])


class Mesh(Object):
    
    _xtk_name = 'mesh'

    def __init__(self, url, magicmode=False, opacity=1.0, color=(1.0,1.0,1.0)):
        super(Mesh,self).__init__(magicmode=magicmode, opacity=opacity, color=color)
        self.url = url

    def generate_js_fragment(self):
        js = super(Mesh,self).generate_js_fragment()
        js += '    %s.file = "%s";\n' % (self.var, self.url)
        return js


class Sphere(Object):
    
    _xtk_name = 'sphere'

    def __init__(self, center, radius, magicmode=False, opacity=1.0, color=(1.0,1.0,1.0)):
        super(Sphere,self).__init__(magicmode=magicmode, opacity=opacity, color=color)
        self.center = center
        self.radius = radius

    def generate_js_fragment(self):
        js = super(Sphere,self).generate_js_fragment()
        js += '    %s.center = [%f,%f,%f];\n' % (self.var, self.center[0], self.center[1], self.center[2])
        js += '    %s.radius = %f;\n' % (self.var, self.radius)
        return js


class Cylinder(Object):
    
    _xtk_name = 'cylinder'

    def __init__(self, start, end, radius, magicmode=False, opacity=1.0, color=(1.0,1.0,1.0)):
        super(Cylinder,self).__init__(magicmode=magicmode, opacity=opacity, color=color)
        self.start = start
        self.end = end
        self.radius = radius

    def generate_js_fragment(self):
        js = super(Cylinder,self).generate_js_fragment()
        js += '    %s.start = [%f,%f,%f];\n' % (self.var, self.start[0], self.start[1], self.start[2])
        js += '    %s.end = [%f,%f,%f];\n' % (self.var, self.end[0], self.end[1], self.end[2])
        js += '    %s.radius = %f;\n' % (self.var, self.radius)
        return js


class Cube(Object):
    
    _xtk_name = 'cube'

    def __init__(self, center, lengths, magicmode=False, opacity=1.0, color=(1.0,1.0,1.0)):
        super(Cube,self).__init__(magicmode=magicmode, opacity=opacity, color=color)
        self.center = center
        self.lengths = lengths

    def generate_js_fragment(self):
        js = super(Cube,self).generate_js_fragment()
        js += '    %s.center = [%f,%f,%f];\n' % (self.var, self.center[0], self.center[1], self.center[2])
        js += '    %s.lengthX = %f;\n' % (self.var, self.lengths[0])
        js += '    %s.lengthY = %f;\n' % (self.var, self.lengths[1])
        js += '    %s.lengthZ = %f;\n' % (self.var, self.lengths[2])
        return js


_renderer3d_template = """
    container.show();
    var id = 'xtkwidget_' + utils.uuid();
    var xtkdiv = $('<div/>').attr('id',id);
    xtkdiv.css('background-color','%s').width(%i).height(%i);
    element.append(xtkdiv);
    var %s = new X.%s();
    %s.container = id;
    %s.init();
"""


class Renderer3D(Base):

    _xtk_name = 'renderer3D'

    def __init__(self, width=400, height=300, bgcolor='#000'):
        super(Renderer3D,self).__init__()
        self.width = width
        self.height = height
        self.bgcolor = bgcolor
        self._objects = []

    def add(self, o):
        self._objects.append(o)

    def render(self):
        display(Javascript(self._repr_javascript_()))

    def _repr_javascript_(self):
        js = _renderer3d_template % (self.bgcolor, self.width, self.height,
            self.var, self._xtk_name, self.var, self.var)
        for o in self._objects:
            js += o.generate_js_fragment()
            js += '    %s.add(%s);\n' % (self.var, o.var)
        js += '    %s.render();\n' % self.var
        js = Javascript(js)
        print js._repr_javascript_()
        return js._repr_javascript_()


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

    r.add(m);
    r.render();
"""


class OldMesh(object):
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

