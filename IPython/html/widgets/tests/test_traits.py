"""Test trait types of the widget packages."""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from unittest import TestCase
from IPython.utils.traitlets import HasTraits
from IPython.utils.tests.test_traitlets import TraitTestBase
from IPython.html.widgets import Color


class ColorTrait(HasTraits):
    value = Color("black")


class TestColor(TraitTestBase):
    obj = ColorTrait()

    _good_values = ["blue", "#AA0", "#FFFFFF"]
    _bad_values = ["vanilla", "blues"]
