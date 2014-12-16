"""Test Notebook signing"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import copy
import time

from .base import TestsBase

from IPython.nbformat import read, sign
from IPython.core.getipython import get_ipython


class TestNotary(TestsBase):
    
    def setUp(self):
        self.notary = sign.NotebookNotary(
            db_file=':memory:',
            secret=b'secret',
            profile_dir=get_ipython().profile_dir,
        )
        with self.fopen(u'test3.ipynb', u'r') as f:
            self.nb = read(f, as_version=4)
        with self.fopen(u'test3.ipynb', u'r') as f:
            self.nb3 = read(f, as_version=3)
    
    def test_algorithms(self):
        last_sig = ''
        for algo in sign.algorithms:
            self.notary.algorithm = algo
            sig = self.notary.compute_signature(self.nb)
            self.assertNotEqual(last_sig, sig)
            last_sig = sig
    
    def test_sign_same(self):
        """Multiple signatures of the same notebook are the same"""
        sig1 = self.notary.compute_signature(self.nb)
        sig2 = self.notary.compute_signature(self.nb)
        self.assertEqual(sig1, sig2)
    
    def test_change_secret(self):
        """Changing the secret changes the signature"""
        sig1 = self.notary.compute_signature(self.nb)
        self.notary.secret = b'different'
        sig2 = self.notary.compute_signature(self.nb)
        self.assertNotEqual(sig1, sig2)
    
    def test_sign(self):
        self.assertFalse(self.notary.check_signature(self.nb))
        self.notary.sign(self.nb)
        self.assertTrue(self.notary.check_signature(self.nb))
    
    def test_unsign(self):
        self.notary.sign(self.nb)
        self.assertTrue(self.notary.check_signature(self.nb))
        self.notary.unsign(self.nb)
        self.assertFalse(self.notary.check_signature(self.nb))
        self.notary.unsign(self.nb)
        self.assertFalse(self.notary.check_signature(self.nb))
    
    def test_cull_db(self):
        # this test has various sleeps of 2ms
        # to ensure low resolution timestamps compare as expected
        dt = 2e-3
        nbs = [
            copy.deepcopy(self.nb) for i in range(10)
        ]
        for row in self.notary.db.execute("SELECT * FROM nbsignatures"):
            print(row)
        self.notary.cache_size = 8
        for i, nb in enumerate(nbs[:8]):
            nb.metadata.dirty = i
            self.notary.sign(nb)
        
        for i, nb in enumerate(nbs[:8]):
            time.sleep(dt)
            self.assertTrue(self.notary.check_signature(nb), 'nb %i is trusted' % i)
        
        # signing the 9th triggers culling of first 3
        # (75% of 8 = 6, 9 - 6 = 3 culled)
        self.notary.sign(nbs[8])
        self.assertFalse(self.notary.check_signature(nbs[0]))
        self.assertFalse(self.notary.check_signature(nbs[1]))
        self.assertFalse(self.notary.check_signature(nbs[2]))
        self.assertTrue(self.notary.check_signature(nbs[3]))
        # checking nb3 should keep it from being culled:
        self.notary.sign(nbs[0])
        self.notary.sign(nbs[1])
        self.notary.sign(nbs[2])
        self.assertTrue(self.notary.check_signature(nbs[3]))
        self.assertFalse(self.notary.check_signature(nbs[4]))
    
    def test_check_signature(self):
        nb = self.nb
        md = nb.metadata
        notary = self.notary
        check_signature = notary.check_signature
        # no signature:
        md.pop('signature', None)
        self.assertFalse(check_signature(nb))
        # hash only, no algo
        md.signature = notary.compute_signature(nb)
        self.assertFalse(check_signature(nb))
        # proper signature, algo mismatch
        notary.algorithm = 'sha224'
        notary.sign(nb)
        notary.algorithm = 'sha256'
        self.assertFalse(check_signature(nb))
        # check correctly signed notebook
        notary.sign(nb)
        self.assertTrue(check_signature(nb))
    
    def test_mark_cells_untrusted(self):
        cells = self.nb.cells
        self.notary.mark_cells(self.nb, False)
        for cell in cells:
            self.assertNotIn('trusted', cell)
            if cell.cell_type == 'code':
                self.assertIn('trusted', cell.metadata)
                self.assertFalse(cell.metadata.trusted)
            else:
                self.assertNotIn('trusted', cell.metadata)
    
    def test_mark_cells_trusted(self):
        cells = self.nb.cells
        self.notary.mark_cells(self.nb, True)
        for cell in cells:
            self.assertNotIn('trusted', cell)
            if cell.cell_type == 'code':
                self.assertIn('trusted', cell.metadata)
                self.assertTrue(cell.metadata.trusted)
            else:
                self.assertNotIn('trusted', cell.metadata)
    
    def test_check_cells(self):
        nb = self.nb
        self.notary.mark_cells(nb, True)
        self.assertTrue(self.notary.check_cells(nb))
        for cell in nb.cells:
            self.assertNotIn('trusted', cell)
        self.notary.mark_cells(nb, False)
        self.assertFalse(self.notary.check_cells(nb))
        for cell in nb.cells:
            self.assertNotIn('trusted', cell)
    
    def test_trust_no_output(self):
        nb = self.nb
        self.notary.mark_cells(nb, False)
        for cell in nb.cells:
            if cell.cell_type == 'code':
                cell.outputs = []
        self.assertTrue(self.notary.check_cells(nb))
    
    def test_mark_cells_untrusted_v3(self):
        nb = self.nb3
        cells = nb.worksheets[0].cells
        self.notary.mark_cells(nb, False)
        for cell in cells:
            self.assertNotIn('trusted', cell)
            if cell.cell_type == 'code':
                self.assertIn('trusted', cell.metadata)
                self.assertFalse(cell.metadata.trusted)
            else:
                self.assertNotIn('trusted', cell.metadata)
    
    def test_mark_cells_trusted_v3(self):
        nb = self.nb3
        cells = nb.worksheets[0].cells
        self.notary.mark_cells(nb, True)
        for cell in cells:
            self.assertNotIn('trusted', cell)
            if cell.cell_type == 'code':
                self.assertIn('trusted', cell.metadata)
                self.assertTrue(cell.metadata.trusted)
            else:
                self.assertNotIn('trusted', cell.metadata)
    
    def test_check_cells_v3(self):
        nb = self.nb3
        cells = nb.worksheets[0].cells
        self.notary.mark_cells(nb, True)
        self.assertTrue(self.notary.check_cells(nb))
        for cell in cells:
            self.assertNotIn('trusted', cell)
        self.notary.mark_cells(nb, False)
        self.assertFalse(self.notary.check_cells(nb))
        for cell in cells:
            self.assertNotIn('trusted', cell)
        

