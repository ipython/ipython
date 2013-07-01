import re
import nose.tools as nt
from converters.base import clean_filename


def test_clean_filename():
    good_chars = re.compile('^[a-zA-Z0-9_]+$')

    def check_str(s):
        nt.assert_true(good_chars.match(clean_filename(s)) is not None)

    strings = [
        'abCaBdX0753--$++()',
        '()$(@dasdk_%^^&&($#*@',
        '%(#)@#@%^(^#DKDOPSfks0943k',
        '439DDxsx___dsaigfj6&^',
        '\'sdf594,,<<.>>/"""\'\'{}||]]'
    ]
    for s in strings:
        yield check_str, s
