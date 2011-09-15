# coding: utf-8
"""
GLUT Inputhook support functions
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

# GLUT is quite an old library and it is difficult to ensure proper
# integration within IPython since original GLUT does not allow to handle
# events one by one. Instead, it requires for the mainloop to be entered
# and never returned (there is not even a function to exit he
# mainloop). Fortunately, there are alternatives such as freeglut
# (available for linux and windows) and the OSX implementation gives
# access to a glutCheckLoop() function that blocks itself until a new
# event is received. This means we have to setup a default timer to
# ensure we got at least one event that will unblock the function. We set
# a default timer of 60fps.
#
# Furthermore, it is not possible to install these handlers without a
# window being first created. We choose to make this window invisible and
# the user is supposed to make it visible when needed (see gui-glut.py in
# the docs/examples/lib directory). This means that display mode options
# are set at this level and user won't be able to change them later
# without modifying the code. This should probably be made available via
# IPython options system.

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import sys
import time
import signal
import OpenGL
OpenGL.ERROR_CHECKING = False
import OpenGL.GLUT as glut
import OpenGL.platform as platform

#-----------------------------------------------------------------------------
# Constants
#-----------------------------------------------------------------------------

# Frame per second : 60
# Should probably be an IPython option
glut_fps = 60
        

# Display mode : double buffeed + rgba + depth
# Should probably be an IPython option
glut_display_mode = (glut.GLUT_DOUBLE |
                     glut.GLUT_RGBA   |
                     glut.GLUT_DEPTH)

glutMainLoopEvent = None
if sys.platform == 'darwin':
    try:
        glutCheckLoop = platform.createBaseFunction( 
            'glutCheckLoop', dll=platform.GLUT, resultType=None, 
            argTypes=[],
            doc='glutCheckLoop(  ) -> None', 
            argNames=(),
            )
    except AttributeError:
        raise RuntimeError(
            '''Your glut implementation does not allow interactive sessions'''
            '''Consider installing freeglut.''')
    glutMainLoopEvent = glutCheckLoop
elif glut.HAVE_FREEGLUT:
    glutMainLoopEvent = glut.glutMainLoopEvent
else:
    raise RuntimeError(
        '''Your glut implementation does not allow interactive sessions. '''
        '''Consider installing freeglut.''')


#-----------------------------------------------------------------------------
# Callback functions
#-----------------------------------------------------------------------------

def glut_display():
    # Dummy display function
    pass

def glut_timer(fps):
    # We should normally set the active window to 1 and post a
    # redisplay for each window.  The problem is that we do not know
    # how much active windows we have and there is no function in glut
    # to get that number.
    # glut.glutSetWindow(1)
    glut.glutTimerFunc( int(1000.0/fps), glut_timer, fps)
    glut.glutPostRedisplay()

def glut_close():
    glut.glutHideWindow()


def glut_int_handler(signum, frame):
    signal.signal(signal.SIGINT, signal.default_int_handler)
    print '\nKeyboardInterrupt'
    # Need to reprint the prompt at this stage



def inputhook_glut():
    """ Process pending GLUT events only. """            

    # We need to protect against a user pressing Control-C when IPython
    # is idle and this is running. We should trap KeyboardInterrupt and
    # pass but it does not seem to work with glutMainLoopEvent.
    # Instead, we setup a signal handler on SIGINT and returns after
    # having restored the default python SIGINT handler.
    signal.signal(signal.SIGINT, glut_int_handler)
    try:
        glutMainLoopEvent()
    except KeyboardInterrupt: # this catch doesn't work for some reasons...
        pass
    return 0


