"""Manual test for figure.show() in the inline matplotlib backend.

This script should be loaded for interactive use (via %load) into a qtconsole
or notebook initialized with the pylab inline backend.  

Expected behavior: only *one* copy of the figure is shown.


For further details:
https://github.com/ipython/ipython/issues/1612
https://github.com/matplotlib/matplotlib/issues/835
"""

import numpy as np
import matplotlib.pyplot as plt

plt.ioff()                                                                      
x = np.random.uniform(-5, 5, size=(100))
y = np.random.uniform(-5, 5, size=(100))
f = plt.figure()
plt.scatter(x, y)
plt.plot(y)
f.show()
