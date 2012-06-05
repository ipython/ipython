"""Tests for Octave magics extension."""

import nose.tools as nt

try:
    import oct2py
    import numpy as np
    import numpy.testing as npt

    from IPython.extensions import octavemagic
except Exception, e:
    __test__ = False

global octave

def setup():
    ip = get_ipython()
    global octave

    octave = octavemagic.OctaveMagics(ip)
    ip.register_magics(octave)

    ip.ex('import numpy as np')

def test_octave_inline():
    ip = get_ipython()
    result = ip.run_line_magic('octave', '[1, 2, 3] + 1;')
    npt.assert_array_equal(result, [[2, 3, 4]])

def test_octave_roundtrip():
    ip = get_ipython()
    ip.ex('x = np.arange(3); y = 4.5')
    ip.run_line_magic('octave_push', 'x y')
    ip.run_line_magic('octave', 'x = x + 1; y = y + 1;')
    ip.run_line_magic('octave_pull', 'x y')

    npt.assert_array_equal(ip.user_ns['x'], [[1, 2, 3]])
    nt.assert_equal(ip.user_ns['y'], 5.5)

def test_octave_cell_magic():
    ip = get_ipython()
    ip.ex('x = 3; y = [1, 2]')
    ip.run_cell_magic('octave', '-f png -s 400,400 -i x,y -o z',
                      'z = x + y;')
    npt.assert_array_equal(ip.user_ns['z'], [[4, 5]])


def verify_publish_data(source, data):
    if 'image/svg+xml' in data:
        svg = data['image/svg+xml']
        assert 'height="500px"' in svg
        assert 'width="400px"' in svg

        test_octave_plot.svgs_generated += 1

def test_octave_plot():
    octave._publish_display_data = verify_publish_data
    test_octave_plot.svgs_generated = 0

    ip = get_ipython()
    ip.run_cell_magic('octave', '-f svg -s 400,500',
                      'plot([1, 2, 3]); figure; plot([4, 5, 6]);')

    nt.assert_equal(test_octave_plot.svgs_generated, 2)
