import io
import nose.tools as nt
from nose.tools import nottest

from converters.latex_transformer import remove_math_space

@nottest
def test_space(input, reference):
    nt.assert_equal(remove_math_space(input),reference)
    


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
