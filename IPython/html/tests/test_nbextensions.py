# coding: utf-8
"""Test installation of notebook extensions"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

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
        self.save_system_dir = nbextensions.SYSTEM_NBEXTENSIONS_INSTALL_DIR
        nbextensions.SYSTEM_NBEXTENSIONS_INSTALL_DIR = self.system_nbext = self.tempdir()
    
    def tearDown(self):
        nbextensions.get_ipython_dir = self.save_get_ipython_dir
        nbextensions.SYSTEM_NBEXTENSIONS_INSTALL_DIR = self.save_system_dir
        for td in self.tempdirs:
            td.cleanup()

    def assert_dir_exists(self, path):
        if not os.path.exists(path):
            do_exist = os.listdir(os.path.dirname(path))
            self.fail(u"%s should exist (found %s)" % (path, do_exist))
    
    def assert_not_dir_exists(self, path):
        if os.path.exists(path):
            self.fail(u"%s should not exist" % path)
    
    def assert_installed(self, relative_path, user=False):
        if user:
            nbext = pjoin(self.ipdir, u'nbextensions')
        else:
            nbext = self.system_nbext
        self.assert_dir_exists(
            pjoin(nbext, relative_path)
        )
    
    def assert_not_installed(self, relative_path, user=False):
        if user:
            nbext = pjoin(self.ipdir, u'nbextensions')
        else:
            nbext = self.system_nbext
        self.assert_not_dir_exists(
            pjoin(nbext, relative_path)
        )
    
    def test_create_ipython_dir(self):
        """install_nbextension when ipython_dir doesn't exist"""
        with TemporaryDirectory() as td:
            self.ipdir = ipdir = pjoin(td, u'ipython')
            install_nbextension(self.src, user=True)
            self.assert_dir_exists(ipdir)
            for file in self.files:
                self.assert_installed(
                    pjoin(basename(self.src), file),
                    user=bool(ipdir)
                )
    
    def test_create_nbextensions_user(self):
        with TemporaryDirectory() as td:
            self.ipdir = ipdir = pjoin(td, u'ipython')
            install_nbextension(self.src, user=True)
            self.assert_installed(
                pjoin(basename(self.src), u'ƒile'),
                user=True
            )
    
    def test_create_nbextensions_system(self):
        with TemporaryDirectory() as td:
            nbextensions.SYSTEM_NBEXTENSIONS_INSTALL_DIR = self.system_nbext = pjoin(td, u'nbextensions')
            install_nbextension(self.src, user=False)
            self.assert_installed(
                pjoin(basename(self.src), u'ƒile'),
                user=False
            )
    
    def test_single_file(self):
        file = self.files[0]
        install_nbextension(pjoin(self.src, file))
        self.assert_installed(file)
    
    def test_single_dir(self):
        d = u'∂ir'
        install_nbextension(pjoin(self.src, d))
        self.assert_installed(self.files[-1])
    

    def test_destination_file(self):
        file = self.files[0]
        install_nbextension(pjoin(self.src, file), destination = u'ƒiledest')
        self.assert_installed(u'ƒiledest')

    def test_destination_dir(self):
        d = u'∂ir'
        install_nbextension(pjoin(self.src, d), destination = u'ƒiledest2')
        self.assert_installed(pjoin(u'ƒiledest2', u'∂ir2', u'ƒile2'))
    
    def test_install_nbextension(self):
        with self.assertRaises(TypeError):
            install_nbextension(glob.glob(pjoin(self.src, '*')))
    
    def test_overwrite_file(self):
        with TemporaryDirectory() as d:
            fname = u'ƒ.js'
            src = pjoin(d, fname)
            with open(src, 'w') as f:
                f.write('first')
            mtime = touch(src)
            dest = pjoin(self.system_nbext, fname)
            install_nbextension(src)
            with open(src, 'w') as f:
                f.write('overwrite')
            mtime = touch(src, mtime - 100)
            install_nbextension(src, overwrite=True)
            with open(dest) as f:
                self.assertEqual(f.read(), 'overwrite')
    
    def test_overwrite_dir(self):
        with TemporaryDirectory() as src:
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
            dest = pjoin(self.system_nbext, fname)
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
            dest = pjoin(self.system_nbext, fname)
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
            install_nbextension("https://example.com/path/to/another/bar.js", 
                                destination = 'foobar.js')
            self.assert_installed("foobar.js")
        finally:
            nbextensions.urlretrieve = save_urlretrieve
    
    def test_check_nbextension(self):
        with TemporaryDirectory() as d:
            f = u'ƒ.js'
            src = pjoin(d, f)
            touch(src)
            install_nbextension(src, user=True)
        
        assert check_nbextension(f, user=True)
        assert check_nbextension([f], user=True)
        assert not check_nbextension([f, pjoin('dne', f)], user=True)
    
    @dec.skip_win32
    def test_install_symlink(self):
        with TemporaryDirectory() as d:
            f = u'ƒ.js'
            src = pjoin(d, f)
            touch(src)
            install_nbextension(src, symlink=True)
        dest = pjoin(self.system_nbext, f)
        assert os.path.islink(dest)
        link = os.readlink(dest)
        self.assertEqual(link, src)
    
    @dec.skip_win32
    def test_overwrite_broken_symlink(self):
        with TemporaryDirectory() as d:
            f = u'ƒ.js'
            f2 = u'ƒ2.js'
            src = pjoin(d, f)
            src2 = pjoin(d, f2)
            touch(src)
            install_nbextension(src, symlink=True)
            os.rename(src, src2)
            install_nbextension(src2, symlink=True, overwrite=True, destination=f)
        dest = pjoin(self.system_nbext, f)
        assert os.path.islink(dest)
        link = os.readlink(dest)
        self.assertEqual(link, src2)

    @dec.skip_win32
    def test_install_symlink_destination(self):
        with TemporaryDirectory() as d:
            f = u'ƒ.js'
            flink = u'ƒlink.js'
            src = pjoin(d, f)
            touch(src)
            install_nbextension(src, symlink=True, destination=flink)
        dest = pjoin(self.system_nbext, flink)
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

    def test_install_destination_bad(self):
        with TemporaryDirectory() as d:
            zf = u'ƒ.zip'
            zsrc = pjoin(d, zf)
            with zipfile.ZipFile(zsrc, 'w') as z:
                z.writestr("a.js", b"b();")
        
            with self.assertRaises(ValueError):
                install_nbextension(zsrc, destination='foo')
