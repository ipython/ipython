# coding: utf-8
"""Test installation of notebook extensions"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2014 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import glob
import os
import re
import tarfile
import zipfile
from io import BytesIO
from os.path import basename, join as pjoin
from unittest import TestCase

import IPython.testing.tools as tt
import IPython.testing.decorators as dec
from IPython.utils import py3compat
from IPython.utils.tempdir import TemporaryDirectory
from IPython.html import nbextensions
from IPython.html.nbextensions import install_nbextension, check_nbextension

#-----------------------------------------------------------------------------
# Test functions
#-----------------------------------------------------------------------------

def touch(file, mtime=None):
    """ensure a file exists, and set its modification time
    
    returns the modification time of the file
    """
    open(file, 'a').close()
    # set explicit mtime
    if mtime:
        atime = os.stat(file).st_atime
        os.utime(file, (atime, mtime))
    return os.stat(file).st_mtime


class TestInstallNBExtension(TestCase):
    
    def tempdir(self):
        td = TemporaryDirectory()
        self.tempdirs.append(td)
        return py3compat.cast_unicode(td.name)

    def setUp(self):
        self.tempdirs = []
        src = self.src = self.tempdir()
        self.files = files = [
            pjoin(u'ƒile'),
            pjoin(u'∂ir', u'ƒile1'),
            pjoin(u'∂ir', u'∂ir2', u'ƒile2'),
        ]
        for file in files:
            fullpath = os.path.join(self.src, file)
            parent = os.path.dirname(fullpath)
            if not os.path.exists(parent):
                os.makedirs(parent)
            touch(fullpath)
        
        self.ipdir = self.tempdir()
        self.save_get_ipython_dir = nbextensions.get_ipython_dir
        nbextensions.get_ipython_dir = lambda : self.ipdir
    
    def tearDown(self):
        for td in self.tempdirs:
            td.cleanup()
        nbextensions.get_ipython_dir = self.save_get_ipython_dir
    
    def assert_path_exists(self, path):
        if not os.path.exists(path):
            do_exist = os.listdir(os.path.dirname(path))
            self.fail(u"%s should exist (found %s)" % (path, do_exist))
    
    def assert_not_path_exists(self, path):
        if os.path.exists(path):
            self.fail(u"%s should not exist" % path)
    
    def assert_installed(self, relative_path, ipdir=None):
        self.assert_path_exists(
            pjoin(ipdir or self.ipdir, u'nbextensions', relative_path)
        )
    
    def assert_not_installed(self, relative_path, ipdir=None):
        self.assert_not_path_exists(
            pjoin(ipdir or self.ipdir, u'nbextensions', relative_path)
        )
    
    def test_create_ipython_dir(self):
        """install_nbextension when ipython_dir doesn't exist"""
        with TemporaryDirectory() as td:
            ipdir = pjoin(td, u'ipython')
            install_nbextension(self.src, ipython_dir=ipdir)
            self.assert_path_exists(ipdir)
            for file in self.files:
                self.assert_installed(
                    pjoin(basename(self.src), file),
                    ipdir
                )
    
    def test_create_nbextensions(self):
        with TemporaryDirectory() as ipdir:
            install_nbextension(self.src, ipython_dir=ipdir)
            self.assert_installed(
                pjoin(basename(self.src), u'ƒile'),
                ipdir
            )
    
    def test_single_file(self):
        file = self.files[0]
        install_nbextension(pjoin(self.src, file))
        self.assert_installed(file)
    
    def test_single_dir(self):
        d = u'∂ir'
        install_nbextension(pjoin(self.src, d))
        self.assert_installed(self.files[-1])
    
    def test_install_nbextension(self):
        install_nbextension(glob.glob(pjoin(self.src, '*')))
        for file in self.files:
            self.assert_installed(file)
    
    def test_overwrite_file(self):
        with TemporaryDirectory() as d:
            fname = u'ƒ.js'
            src = pjoin(d, fname)
            with open(src, 'w') as f:
                f.write('first')
            mtime = touch(src)
            dest = pjoin(self.ipdir, u'nbextensions', fname)
            install_nbextension(src)
            with open(src, 'w') as f:
                f.write('overwrite')
            mtime = touch(src, mtime - 100)
            install_nbextension(src, overwrite=True)
            with open(dest) as f:
                self.assertEqual(f.read(), 'overwrite')
    
    def test_overwrite_dir(self):
        with TemporaryDirectory() as src:
            # src = py3compat.cast_unicode_py2(src)
            base = basename(src)
            fname = u'ƒ.js'
            touch(pjoin(src, fname))
            install_nbextension(src)
            self.assert_installed(pjoin(base, fname))
            os.remove(pjoin(src, fname))
            fname2 = u'∂.js'
            touch(pjoin(src, fname2))
            install_nbextension(src, overwrite=True)
            self.assert_installed(pjoin(base, fname2))
            self.assert_not_installed(pjoin(base, fname))
    
    def test_update_file(self):
        with TemporaryDirectory() as d:
            fname = u'ƒ.js'
            src = pjoin(d, fname)
            with open(src, 'w') as f:
                f.write('first')
            mtime = touch(src)
            install_nbextension(src)
            self.assert_installed(fname)
            dest = pjoin(self.ipdir, u'nbextensions', fname)
            old_mtime = os.stat(dest).st_mtime
            with open(src, 'w') as f:
                f.write('overwrite')
            touch(src, mtime + 10)
            install_nbextension(src)
            with open(dest) as f:
                self.assertEqual(f.read(), 'overwrite')
    
    def test_skip_old_file(self):
        with TemporaryDirectory() as d:
            fname = u'ƒ.js'
            src = pjoin(d, fname)
            mtime = touch(src)
            install_nbextension(src)
            self.assert_installed(fname)
            dest = pjoin(self.ipdir, u'nbextensions', fname)
            old_mtime = os.stat(dest).st_mtime
            
            mtime = touch(src, mtime - 100)
            install_nbextension(src)
            new_mtime = os.stat(dest).st_mtime
            self.assertEqual(new_mtime, old_mtime)

    def test_quiet(self):
        with tt.AssertNotPrints(re.compile(r'.+')):
            install_nbextension(self.src, verbose=0)
    
    def test_install_zip(self):
        path = pjoin(self.src, "myjsext.zip")
        with zipfile.ZipFile(path, 'w') as f:
            f.writestr("a.js", b"b();")
            f.writestr("foo/a.js", b"foo();")
        install_nbextension(path)
        self.assert_installed("a.js")
        self.assert_installed(pjoin("foo", "a.js"))
    
    def test_install_tar(self):
        def _add_file(f, fname, buf):
            info = tarfile.TarInfo(fname)
            info.size = len(buf)
            f.addfile(info, BytesIO(buf))
        
        for i,ext in enumerate((".tar.gz", ".tgz", ".tar.bz2")):
            path = pjoin(self.src, "myjsext" + ext)
            with tarfile.open(path, 'w') as f:
                _add_file(f, "b%i.js" % i, b"b();")
                _add_file(f, "foo/b%i.js" % i, b"foo();")
            install_nbextension(path)
            self.assert_installed("b%i.js" % i)
            self.assert_installed(pjoin("foo", "b%i.js" % i))
    
    def test_install_url(self):
        def fake_urlretrieve(url, dest):
            touch(dest)
        save_urlretrieve = nbextensions.urlretrieve
        nbextensions.urlretrieve = fake_urlretrieve
        try:
            install_nbextension("http://example.com/path/to/foo.js")
            self.assert_installed("foo.js")
            install_nbextension("https://example.com/path/to/another/bar.js")
            self.assert_installed("bar.js")
        finally:
            nbextensions.urlretrieve = save_urlretrieve
    
    def test_check_nbextension(self):
        with TemporaryDirectory() as d:
            f = u'ƒ.js'
            src = pjoin(d, f)
            touch(src)
            install_nbextension(src)
        
        assert check_nbextension(f, self.ipdir)
        assert check_nbextension([f], self.ipdir)
        assert not check_nbextension([f, pjoin('dne', f)], self.ipdir)
    
    @dec.skip_win32
    def test_install_symlink(self):
        with TemporaryDirectory() as d:
            f = u'ƒ.js'
            src = pjoin(d, f)
            touch(src)
            install_nbextension(src, symlink=True)
        dest = pjoin(self.ipdir, u'nbextensions', f)
        assert os.path.islink(dest)
        link = os.readlink(dest)
        self.assertEqual(link, src)
    
    def test_install_symlink_bad(self):
        with self.assertRaises(ValueError):
            install_nbextension("http://example.com/foo.js", symlink=True)
        
        with TemporaryDirectory() as d:
            zf = u'ƒ.zip'
            zsrc = pjoin(d, zf)
            with zipfile.ZipFile(zsrc, 'w') as z:
                z.writestr("a.js", b"b();")
        
            with self.assertRaises(ValueError):
                install_nbextension(zsrc, symlink=True)

