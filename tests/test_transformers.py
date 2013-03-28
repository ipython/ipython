import io
import nose.tools as nt
from nose.tools import nottest

from converters.latex_transformer import rm_math_space

@nottest
def test_space(input, reference):
    nt.assert_equal(rm_math_space(input),reference)

def test_evens():
    unchanged = [
        """
        you should be able to type

            $ a single dollar and go to the line

        it shouldn't be transformed.
        """
            ]
    references = [
            ('$e$','$e$'),
            ('$ e $','$e$'),
            ('xxx$e^i$yyy','xxx$e^i$yyy'),
            ('xxx$ e^i $yyy','xxx$e^i$yyy'),
            ('xxx$e^i $yyy','xxx$e^i$yyy'),
            ('xxx$ e^i$yyy','xxx$e^i$yyy'),
            ('\$ e $ e $','\$ e $e$'),
            ('',''),
            ]

    for k,v in references :
        yield test_space, k,v

    for unch in unchanged :
        yield test_space, unch, unch