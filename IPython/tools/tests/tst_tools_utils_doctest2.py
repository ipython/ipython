# Setup - all imports are done in tcommon
from IPython.testing import tcommon
from IPython.testing.tcommon import *

# Doctest code begins here
from IPython.tools import utils

# Some other tests for utils

utils.marquee('Testing marquee')

utils.marquee('Another test',30,'.')

