"""Base TestCase class for testing Exporters"""

#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import os

from IPython.testing.decorators import onlyif_any_cmd_exists

from ...tests.base import TestsBase

#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

all_raw_mimetypes = {
    'text/x-python',
    'text/markdown',
    'text/html',
    'text/restructuredtext',
    'text/latex',
}

class ExportersTestsBase(TestsBase):
    """Contains base test functions for exporters"""
    
    exporter_class = None
    should_include_raw = None
    
    def _get_notebook(self, nb_name='notebook2.ipynb'):
        return os.path.join(self._get_files_path(), nb_name)
    
    @onlyif_any_cmd_exists('nodejs', 'node', 'pandoc')
    def test_raw_cell_inclusion(self):
        """test raw cell inclusion based on raw_mimetype metadata"""
        if self.should_include_raw is None:
            return
        exporter = self.exporter_class()
        (output, resources) = exporter.from_filename(self._get_notebook('rawtest.ipynb'))
        for inc in self.should_include_raw:
            self.assertIn('raw %s' % inc, output, "should include %s" % inc)
        self.assertIn('no raw_mimetype metadata', output)
        for exc in all_raw_mimetypes.difference(self.should_include_raw):
            self.assertNotIn('raw %s' % exc, output, "should exclude %s" % exc)
        self.assertNotIn('never be included', output)
