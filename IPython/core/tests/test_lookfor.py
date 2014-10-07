import tempfile, os

from IPython.config.loader import Config
import nose.tools as nt

ip = get_ipython()
ip.magic('load_ext lookfor')

def test_store_restore():
    ip.magic('lookfor linalg numpy')
    ip.magic('lookfor linalg scipy')

