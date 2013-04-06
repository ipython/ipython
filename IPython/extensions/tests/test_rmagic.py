from StringIO import StringIO

import numpy as np
from IPython.core.interactiveshell import InteractiveShell
from IPython.testing.decorators import skip_without
from IPython.extensions import rmagic
from rpy2 import rinterface
import nose.tools as nt

ip = get_ipython()
ip.magic('load_ext rmagic')


def test_push():
    rm = rmagic.RMagics(ip)
    ip.push({'X':np.arange(5), 'Y':np.array([3,5,4,6,7])})
    ip.run_line_magic('Rpush', 'X Y')
    np.testing.assert_almost_equal(np.asarray(rm.r('X')), ip.user_ns['X'])
    np.testing.assert_almost_equal(np.asarray(rm.r('Y')), ip.user_ns['Y'])

def test_push_localscope():
    """Test that Rpush looks for variables in the local scope first."""
    ip.run_cell('''
def rmagic_addone(u):
    %Rpush u
    %R result = u+1
    %Rpull result
    return result[0]
u = 0
result = rmagic_addone(12344)
    ''')
    result = ip.user_ns['result']
    np.testing.assert_equal(result, 12345)

@skip_without('pandas')
def test_push_dataframe():
    from pandas import DataFrame
    rm = rmagic.RMagics(ip)
    df = DataFrame([{'a': 1, 'b': 'bar'}, {'a': 5, 'b': 'foo', 'c': 20}])
    ip.push({'df':df})
    ip.run_line_magic('Rpush', 'df')
    
    # This is converted to factors, which are currently converted back to Python
    # as integers, so for now we test its representation in R.
    sio = StringIO()
    rinterface.set_writeconsole(sio.write)
    try:
        rm.r('print(df$b[1])')
        nt.assert_in('[1] bar', sio.getvalue())
    finally:
        rinterface.set_writeconsole(None)
    
    # Values come packaged in arrays, so we unbox them to test.
    nt.assert_equal(rm.r('df$a[2]')[0], 5)
    missing = rm.r('df$c[1]')[0]
    assert np.isnan(missing), missing

def test_pull():
    rm = rmagic.RMagics(ip)
    rm.r('Z=c(11:20)')
    ip.run_line_magic('Rpull', 'Z')
    np.testing.assert_almost_equal(np.asarray(rm.r('Z')), ip.user_ns['Z'])
    np.testing.assert_almost_equal(ip.user_ns['Z'], np.arange(11,21))

def test_Rconverter():
    datapy= np.array([(1, 2.9, 'a'), (2, 3.5, 'b'), (3, 2.1, 'c')], 
          dtype=[('x', '<i4'), ('y', '<f8'), ('z', '|S1')])
    ip.user_ns['datapy'] = datapy
    ip.run_line_magic('Rpush', 'datapy')

    # test to see if a copy is being made
    v = ip.run_line_magic('Rget', '-d datapy')
    w = ip.run_line_magic('Rget', '-d datapy')
    np.testing.assert_almost_equal(w['x'], v['x'])
    np.testing.assert_almost_equal(w['y'], v['y'])
    nt.assert_true(np.all(w['z'] == v['z']))
    np.testing.assert_equal(id(w.data), id(v.data))
    nt.assert_equal(w.dtype, v.dtype)

    ip.run_cell_magic('R', ' -d datar', 'datar=datapy')

    u = ip.run_line_magic('Rget', ' -d datar')
    np.testing.assert_almost_equal(u['x'], v['x'])
    np.testing.assert_almost_equal(u['y'], v['y'])
    nt.assert_true(np.all(u['z'] == v['z']))
    np.testing.assert_equal(id(u.data), id(v.data))
    nt.assert_equal(u.dtype, v.dtype)


def test_cell_magic():

    ip.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})
    snippet = '''
    print(summary(a))
    plot(x, y, pch=23, bg='orange', cex=2)
    plot(x, x)
    print(summary(x))
    r = resid(a)
    xc = coef(a)
    '''
    ip.run_cell_magic('R', '-i x,y -o r,xc -w 150 -u mm a=lm(y~x)', snippet)
    np.testing.assert_almost_equal(ip.user_ns['xc'], [3.2, 0.9])
    np.testing.assert_almost_equal(ip.user_ns['r'], np.array([-0.2,  0.9, -1. ,  0.1,  0.2]))


def test_rmagic_localscope():
    ip.push({'x':0})
    ip.run_line_magic('R', '-i x -o result result <-x+1')
    result = ip.user_ns['result']
    nt.assert_equal(result[0], 1)

    ip.run_cell('''def rmagic_addone(u):
    %R -i u -o result result <- u+1
    return result[0]''')
    ip.run_cell('result = rmagic_addone(1)')
    result = ip.user_ns['result']
    nt.assert_equal(result, 2)

    nt.assert_raises(
        NameError,
        ip.run_line_magic,
        "R",
        "-i var_not_defined 1+1")
