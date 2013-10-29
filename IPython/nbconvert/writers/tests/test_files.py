"""
Module with tests for files
"""

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

import sys
import os

from ...tests.base import TestsBase
from ..files import FilesWriter
from IPython.utils.py3compat import PY3

if PY3:
    from io import StringIO
else:
    from StringIO import StringIO


#-----------------------------------------------------------------------------
# Class
#-----------------------------------------------------------------------------

class Testfiles(TestsBase):
    """Contains test functions for files.py"""

    def test_basic_output(self):
        """Is FilesWriter basic output correct?"""

        # Work in a temporary directory.
        with self.create_temp_cwd():

            # Create the resoruces dictionary
            res = {}

            # Create files writer, test output
            writer = FilesWriter()
            writer.write(u'y', res, notebook_name="z")

            # Check the output of the file
            with open('z', 'r') as f:
                output = f.read()
                self.assertEqual(output, u'y')

    def test_ext(self):
        """Does the FilesWriter add the correct extension to the output?"""

        # Work in a temporary directory.
        with self.create_temp_cwd():

            # Create the resoruces dictionary
            res = {'output_extension': 'txt'}

            # Create files writer, test output
            writer = FilesWriter()
            writer.write(u'y', res, notebook_name="z")

            # Check the output of the file
            assert os.path.isfile('z.txt')
            with open('z.txt', 'r') as f:
                output = f.read()
                self.assertEqual(output, u'y')


    def test_extract(self):
        """Can FilesWriter write extracted figures correctly?"""

        # Work in a temporary directory.
        with self.create_temp_cwd():

            # Create the resoruces dictionary
            res = {'outputs': {os.path.join('z_files', 'a'): b'b'}}

            # Create files writer, test output
            writer = FilesWriter()
            writer.write(u'y', res, notebook_name="z")

            # Check the output of the file
            with open('z', 'r') as f:
                output = f.read()
                self.assertEqual(output, u'y')

            # Check the output of the extracted file
            extracted_file_dest = os.path.join('z_files', 'a')
            assert os.path.isfile(extracted_file_dest)
            with open(extracted_file_dest, 'r') as f:
                output = f.read()
                self.assertEqual(output, 'b')


    def test_builddir(self):
        """Can FilesWriter write to a build dir correctly?"""

        # Work in a temporary directory.
        with self.create_temp_cwd():

            # Create the resoruces dictionary
            res = {'outputs': {os.path.join('z_files', 'a'): b'b'}}

            # Create files writer, test output
            writer = FilesWriter()
            writer.build_directory = u'build'
            writer.write(u'y', res, notebook_name="z")

            # Check the output of the file
            assert os.path.isdir(writer.build_directory)
            dest = os.path.join(writer.build_directory, 'z')
            with open(dest, 'r') as f:
                output = f.read()
                self.assertEqual(output, u'y')

            # Check the output of the extracted file
            extracted_file_dest = os.path.join(writer.build_directory, 'z_files', 'a')
            assert os.path.isfile(extracted_file_dest)
            with open(extracted_file_dest, 'r') as f:
                output = f.read()
                self.assertEqual(output, 'b')


    def test_links(self):
        """Can the FilesWriter handle linked files correctly?"""

        # Work in a temporary directory.
        with self.create_temp_cwd():

            # Create test file
            os.mkdir('sub')
            with open(os.path.join('sub', 'c'), 'w') as f:
                f.write('d')

            # Create the resoruces dictionary
            res = {}

            # Create files writer, test output
            writer = FilesWriter()
            writer.files = [os.path.join('sub', 'c')]
            writer.build_directory = u'build'
            writer.write(u'y', res, notebook_name="z")

            # Check the output of the file
            assert os.path.isdir(writer.build_directory)
            dest = os.path.join(writer.build_directory, 'z')
            with open(dest, 'r') as f:
                output = f.read()
                self.assertEqual(output, u'y')

            # Check to make sure the linked file was copied
            path = os.path.join(writer.build_directory, 'sub')
            assert os.path.isdir(path)
            dest = os.path.join(path, 'c')
            assert os.path.isfile(dest)
            with open(dest, 'r') as f:
                output = f.read()
                self.assertEqual(output, 'd')
