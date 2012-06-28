import numpy as np
from IPython.core.interactiveshell import InteractiveShell
from IPython.extensions import rmagic
from itertools import product
import nose.tools as nt

ip = get_ipython()
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

    ip.run_cell_magic('R', ' -d datar  datar=datapy', '')

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
    ip.run_cell_magic('R', '-i x,y -o r,xc a=lm(y~x)', snippet)
    np.testing.assert_almost_equal(ip.user_ns['xc'], [3.2, 0.9])
    np.testing.assert_almost_equal(ip.user_ns['r'], np.array([-0.2,  0.9, -1. ,  0.1,  0.2]))

def test_plotting_args():

    # png

    ip.push({'x':np.arange(5), 'y':np.array([3,5,4,6,7])})

    cell = '''
    plot(x, y, pch=23, bg='orange', cex=2)
    '''
    
    png_px_args = [' '.join(('--units=px',w,h,p)) for 
                   w, h, p in product(['--width=400 ',''],
                                      ['--height=400',''],
                                      ['-p=10', ''])]

    for line in png_px_args:
        ip.run_line_magic('Rdevice', 'png')
        yield ip.run_cell_magic, 'R', line, cell

    basic_args = [' '.join((w,h,p)) for w, h, p in product(['--width=6 ',''],
                                                           ['--height=6',''],
                                                           ['-p=10', ''])]

    for line in basic_args:
        ip.run_line_magic('Rdevice', 'svg')
        yield ip.run_cell_magic, 'R', line, cell

    png_args = ['--units=in --res=1 ' + s for s in basic_args]
    for line in png_args:
        ip.run_line_magic('Rdevice', 'png')
        yield ip.run_cell_magic, 'R', line, cell


