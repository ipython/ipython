"""Test the new %gui command.  Run this in ipython as

In [1]: %gui [backend]

In [2]: %run switchgui [backend]

where the optional backend can be one of:  qt4, gtk, tk, wx.
"""

import sys
import time

from  IPython.lib import inputhook

gui = inputhook.current_gui()
if gui is None:
    gui = 'qt4'
    inputhook.enable_qt4(app=True)

backends = dict(wx='wxagg', qt4='qt4agg', gtk='gtkagg', tk='tkagg')

import matplotlib
matplotlib.use(backends[gui])
matplotlib.interactive(True)

import matplotlib
from matplotlib import pyplot as plt, mlab, pylab
import numpy as np

from numpy import *
from matplotlib.pyplot import *

x = np.linspace(0,pi,500)

print "A plot has been created"
line, = plot(x,sin(2*x))
inputhook.spin()


print "Now, we will update the plot..."
print
for i in range(1,51):
    print i, 
    sys.stdout.flush()
    line.set_data(x,sin(x*i))
    plt.title('i=%d' % i)
    plt.draw()
    inputhook.spin()
