"""Test the new %gui command.  Run this in ipython as

%run switchgui [backend]

where the optional backend can be one of:  qt4, gtk, tk, wx.
"""

import sys
import time

import IPython.core.ipapi as ipapi
ip = ipapi.get()

from  IPython.lib import inputhook

try:
    backend = sys.argv[1]
    #a = ip.magic('gui -a %s' % backend)
    #a = ip.magic('gui %s' % backend)
except IndexError:
    backend = 'qt'

backends = dict(wx='wxagg', qt='qt4agg', gtk='gtkagg', tk='tkagg')

import matplotlib
matplotlib.use(backends[backend])
#matplotlib.interactive(True)

import matplotlib
from matplotlib import pyplot as plt, mlab, pylab
import numpy as np

from numpy import *
from matplotlib.pyplot import *

x = np.linspace(0,pi,100)

print "A plot has been created"
line, = plot(x,sin(2*x))
plt.show()
inputhook.spin_qt4()

#raw_input("Press Enter to continue")

print "I will now count until 10, please hit Ctrl-C before I'm done..."
print "IPython should stop counting and return to the prompt without crashing."
print
line_x = line.get_data()[0]
for i in range(1,51):
    print i, 
    sys.stdout.flush()
    line.set_data(line_x,sin(x*i))
    plt.title('i=%d' % i)
    #plt.show()
    plt.draw()
    inputhook.spin_qt4()
    #time.sleep(0.04)
