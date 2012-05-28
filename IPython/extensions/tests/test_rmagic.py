import numpy as np
from IPython.core.interactiveshell import InteractiveShell
from IPython.extensions import rmagic

ip = None
def setup():
    global ip
    ip = InteractiveShell()
    ip.magic('load_ext rmagic')

def test_push():
    rm = rmagic.RMagics(ip)
    ip.push({'X':np.arange(5), 'Y':np.array([3,5,4,6,7])})
    ip.run_line_magic('Rpush', 'X Y')
    np.testing.assert_almost_equal(np.asarray(rm.r('X')), ip.user_ns['X'])
    np.testing.assert_almost_equal(np.asarray(rm.r('Y')), ip.user_ns['Y'])

def test_pull():
    rm = rmagic.RMagics(ip)
    rm.r('Z=c(11:20)')
    ip.run_line_magic('Rpull', 'Z')
    np.testing.assert_almost_equal(np.asarray(rm.r('Z')), ip.user_ns['Z'])
    np.testing.assert_almost_equal(ip.user_ns['Z'], np.arange(11,21))

def test_inline():
    rm = rmagic.RMagics(ip)
    c = ip.run_line_magic('Rinline', 'lm(Y~X)$coef')
    np.testing.assert_almost_equal(c, [3.2, 0.9])

def test_cell_magic():

    ip.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})
    snippet = '''
    a=lm(y~x)
    print(summary(a))
    plot(X, Y, pch=23, bg='orange', cex=2)
    plot(Y, X)
    print(summary(X))
    r = resid(a)
    xc = coef(a)
    '''
    ip.run_cell_magic('R', '-i x,y -o r,xc', snippet)
    np.testing.assert_almost_equal(ip.user_ns['xc'], [3.2, 0.9])
    np.testing.assert_almost_equal(ip.user_ns['r'], np.array([-0.2,  0.9, -1. ,  0.1,  0.2]))
