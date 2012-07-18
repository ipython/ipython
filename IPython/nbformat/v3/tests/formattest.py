# -*- coding: utf8 -*-
import io
import os
import shutil
import tempfile

pjoin = os.path.join

from ..nbbase import (
    NotebookNode,
    new_code_cell, new_text_cell, new_worksheet, new_notebook
)

from ..nbpy import reads, writes, read, write
from .nbexamples import nb0, nb0_py


def open_utf8(fname, mode):
    return io.open(fname, mode=mode, encoding='utf-8')

class NBFormatTest:
    """Mixin for writing notebook format tests"""

    # override with appropriate values in subclasses
    nb0_ref = None
    ext = None
    mod = None
    
    def setUp(self):
        self.wd = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.wd)
    
    def assertNBEquals(self, nba, nbb):
        self.assertEqual(nba, nbb)
        
    def test_writes(self):
        s = self.mod.writes(nb0)
        if self.nb0_ref:
            self.assertEqual(s, self.nb0_ref)

    def test_reads(self):
        s = self.mod.writes(nb0)
        nb = self.mod.reads(s)

    def test_roundtrip(self):
        s = self.mod.writes(nb0)
        self.assertNBEquals(self.mod.reads(s),nb0)

    def test_write_file(self):
        with open_utf8(pjoin(self.wd, "nb0.%s" % self.ext), 'w') as f:
            self.mod.write(nb0, f)
    
    def test_read_file(self):
        with open_utf8(pjoin(self.wd, "nb0.%s" % self.ext), 'w') as f:
            self.mod.write(nb0, f)
        
        with open_utf8(pjoin(self.wd, "nb0.%s" % self.ext), 'r') as f:
            nb = self.mod.read(f)
        


