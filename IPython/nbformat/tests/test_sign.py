"""Test Notebook signing"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2014, The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from .. import sign
from .base import TestsBase

from ..current import read
from IPython.core.getipython import get_ipython

#-----------------------------------------------------------------------------
# Classes and functions
#-----------------------------------------------------------------------------

class TestNotary(TestsBase):
    
    def setUp(self):
        self.notary = sign.NotebookNotary(
            secret=b'secret',
            profile_dir=get_ipython().profile_dir
        )
        with self.fopen(u'test3.ipynb', u'r') as f:
            self.nb = read(f, u'json')
    
    def test_algorithms(self):
        last_sig = ''
        for algo in sign.algorithms:
            self.notary.algorithm = algo
            self.notary.sign(self.nb)
            sig = self.nb.metadata.signature
            print(sig)
            self.assertEqual(sig[:len(self.notary.algorithm)+1], '%s:' % self.notary.algorithm)
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
        self.notary.sign(self.nb)
        sig = self.nb.metadata.signature
        self.assertEqual(sig[:len(self.notary.algorithm)+1], '%s:' % self.notary.algorithm)
    
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
        cells = self.nb.worksheets[0].cells
        self.notary.mark_cells(self.nb, False)
        for cell in cells:
            if cell.cell_type == 'code':
                self.assertIn('trusted', cell)
                self.assertFalse(cell.trusted)
            else:
                self.assertNotIn('trusted', cell)
    
    def test_mark_cells_trusted(self):
        cells = self.nb.worksheets[0].cells
        self.notary.mark_cells(self.nb, True)
        for cell in cells:
            if cell.cell_type == 'code':
                self.assertIn('trusted', cell)
                self.assertTrue(cell.trusted)
            else:
                self.assertNotIn('trusted', cell)
    
    def test_check_cells(self):
        nb = self.nb
        self.notary.mark_cells(nb, True)
        self.assertTrue(self.notary.check_cells(nb))
        for cell in nb.worksheets[0].cells:
            self.assertNotIn('trusted', cell)
        self.notary.mark_cells(nb, False)
        self.assertFalse(self.notary.check_cells(nb))
        for cell in nb.worksheets[0].cells:
            self.assertNotIn('trusted', cell)
    
    def test_trust_no_output(self):
        nb = self.nb
        self.notary.mark_cells(nb, False)
        for cell in nb.worksheets[0].cells:
            if cell.cell_type == 'code':
                cell.outputs = []
        self.assertTrue(self.notary.check_cells(nb))

