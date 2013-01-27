import io
import nose.tools as nt
import os
from nose.tools import nottest
from converters.template import ConverterTemplate


def test_evens():
    reflist = [
            'tests/ipynbref/IntroNumPy.orig'
            ]

    # null template should return empty
    C = ConverterTemplate()
    C.read('tests/ipynbref/IntroNumPy.orig.ipynb')
    result,_ =  C.convert()
    nt.assert_equal(result,'')

