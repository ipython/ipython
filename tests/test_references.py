import io
import nose.tools as nt
from nose.tools import nottest
from converters import (
    ConverterLaTeX, ConverterMarkdown, ConverterPy, ConverterHTML,
    ConverterReveal
)

@nottest
def cleanfile(stn):
    return filter(None, map(unicode.strip, stn.split('\n')))


def test_evens():
    ######
    # for now, we don't need to really run inkscape to extract svg
    # from file, on unix, for test, we monkeypathc it to 'true'
    # which does not fail as doing anything.
    ####
    ConverterLaTeX.inkscape = 'true'

    # commenting rst for now as travis build
    # fail because of pandoc version.
    converters = [
                 #(ConverterRST, 'rst'),
                  (ConverterMarkdown, 'md'),
                  (ConverterLaTeX, 'tex'),
                  (ConverterPy, 'py'),
                  (ConverterHTML, 'html')
                ]
    reflist = [
            'tests/ipynbref/IntroNumPy.orig'
            ]
    for root in reflist:
        for conv, ext in converters:
            yield test_conversion, conv, root + '.ipynb', root + '.' + ext


def test_reveal():
    conv = ConverterReveal
    root = 'tests/ipynbref/reveal.orig'
    return test_conversion, conv, root + '.ipynb', root + '_slides.' + 'html'


@nottest
def compfiles(stra, strb):
    nt.assert_equal(cleanfile(stra),
                    cleanfile(strb))


@nottest
def test_conversion(ConverterClass, ipynb, ref_file):
    converter = ConverterClass(ipynb)
    converter.read()
    cv = converter.convert()
    with io.open(ref_file) as ref:
        value = ref.read()
        compfiles(cv, value)
