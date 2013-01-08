import io
import nose.tools as nt
import os
from nose.tools import nottest
from converters.template import ConverterTemplate


def test_evens():
    reflist = [
            'tests/ipynbref/IntroNumPy.orig'
            ]

    C = ConverterTemplate(tplfile='basic')
    C.read('tests/ipynbref/IntroNumPy.orig.ipynb')
    result =  C.convert()
    nt.assert_equal(result,'')

    # null template should return empty
    C = ConverterTemplate(tplfile='null')
    C.read('tests/ipynbref/IntroNumPy.orig.ipynb')
    result =  C.convert()
    nt.assert_equal(result,'')

