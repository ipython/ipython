"""Test help output of various IPython entry points"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import sys

import pytest
import IPython.testing.tools as tt
from IPython.utils.process import get_output_error_code


def test_ipython_help():
    tt.help_all_output_test()


def test_profile_help():
    tt.help_all_output_test("profile")


def test_profile_list_help():
    tt.help_all_output_test("profile list")


def test_profile_create_help():
    tt.help_all_output_test("profile create")


def test_locate_help():
    tt.help_all_output_test("locate")


def test_locate_profile_help():
    tt.help_all_output_test("locate profile")
