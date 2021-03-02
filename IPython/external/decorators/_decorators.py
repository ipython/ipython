"""
Decorators for labeling and modifying behavior of test objects.

Decorators that merely return a modified version of the original
function object are straightforward. Decorators that return a new
function object need to use
::

  nose.tools.make_decorator(original_function)(decorator)

in returning the decorator, in order to preserve meta-data such as
function name, setup and teardown functions and so on - see
``nose.tools`` for more information.

"""
import unittest
import pytest

skipif = unittest.skipIf
# Yes, it should be unittest.expectedFailre, but that doesn't take
# message in unittest.
knownfailureif = pytest.mark.xfail
