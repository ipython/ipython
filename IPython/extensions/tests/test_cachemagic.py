import tempfile, os

from IPython.config.loader import Config
from IPython.utils import py3compat
import nose.tools as nt

ip = get_ipython()
ip.magic('load_ext cachemagic')

code = py3compat.str_to_unicode("""foo = 78""")

def test_cache_magic():
    path = 'myvars'
    
    # First run.
    ip.run_cell_magic('cache', 'foo --to='+path, code)
    assert ip.user_ns['foo'] == 78
    
    # Second run: load the variable.
    ip.push(dict(foo=79))
    assert ip.user_ns['foo'] == 79
    ip.run_cell_magic('cache', 'foo --to='+path, code)
    assert ip.user_ns['foo'] == 78
    
    # Third run: override the variable.
    ip.run_cell_magic('cache', 'foo -f --to='+path,
        py3compat.str_to_unicode("""foo = 79"""))
    assert ip.user_ns['foo'] == 79
    
    os.remove(path)

