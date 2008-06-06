# Setup - all imports are done in tcommon
from IPython.testutils import tcommon
from IPython.testutils.tcommon import *

# Doctest code begins here
from IPython.tools import utils

# Some other tests for utils

utils.marquee('Testing marquee')

utils.marquee('Another test',30,'.')

