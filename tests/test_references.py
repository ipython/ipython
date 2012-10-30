import os
import io
import nose.tools as nt
from nbconvert import *
from nose.tools import nottest


def test_evens():
    ###### 
    # for now, we don't need to really run inkscape to extract svg 
    # from file, on unix, for test, we monkeypathc it to 'true'
    # which does not fail as doing anything.
    ####
    ConverterLaTeX.inkscape = 'true'

    converters = [(ConverterRST,'rst'),
                  (ConverterMarkdown,'md'),
                  (ConverterLaTeX,'tex'),
                  (ConverterPy,'py'),
                  (ConverterHTML,'html')
                ]
    reflist = [
            'tests/ipynbref/IntroNumPy.orig'
            ]
    for root in reflist :
        for conv,ext in converters:
            yield test_conversion, conv,root+'.ipynb',root+'.'+ext

@nottest
def test_conversion(ConverterClass, ipynb, ref_file):

    converter = ConverterClass(ipynb)
    converter.read()
    cv =converter.convert()
    with io.open(ref_file) as ref:
        value = ref.read()
        nt.assert_equal(cv.split('\n'),value.split('\n'))
    

