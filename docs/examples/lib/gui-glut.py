#!/usr/bin/env python
"""Simple GLUT example to manually test event loop integration.

This is meant to run tests manually in ipython as:

In [5]: %gui glut

In [6]: %run gui-glut.py

In [7]: gl.glClearColor(1,1,1,1)
"""

#!/usr/bin/env python
import sys
import OpenGL.GL as gl
import OpenGL.GLUT as glut

def display():
    gl.glClear (gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    glut.glutSwapBuffers()

def resize(width,height):
    gl.glViewport(0, 0, width, height+4)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    gl.glOrtho(0, width, 0, height+4, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)


if glut.glutGetWindow() > 0:
    interactive = True
    glut.glutInit(sys.argv)
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE |
                             glut.GLUT_RGBA   |
                             glut.GLUT_DEPTH)
    glut.glutShowWindow()
else:
    glut.glutCreateWindow('gui-glut')
    interactive = False

glut.glutDisplayFunc(display)
glut.glutReshapeFunc(resize)
gl.glClearColor(0,0,0,1)

if not interactive:
    glut.glutMainLoop()
