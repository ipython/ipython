import io
import nose.tools as nt
from nose.tools import nottest

from converters import latex_transformer
lt = latex_transformer.LatexTransformer()
lt.enabled = True

@nottest
def test_space(input, reference):
    nt.assert_equal(lt.remove_math_space(input),reference)
    


def test_evens():
    references = [
            ('$e$','$e$'),
            ('$ e $','$e$'),
            ('xxx$e^i$yyy','xxx$e^i$yyy'),
            ('xxx$ e^i $yyy','xxx$e^i$yyy'),
            ('xxx$e^i $yyy','xxx$e^i$yyy'),
            ('xxx$ e^i$yyy','xxx$e^i$yyy'),
            ('\$ e $ e $','\$ e $e$'),
            ]

    for k,v in references :
        yield test_space, k,v
