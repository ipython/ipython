Unicode name completions
========================

Previously, we provided completion for a unicode name with its relative symbol.
With this, now IPython provides complete suggestions to unicode name symbols.

As on the PR, if user types ``\LAT<tab>``, IPython provides a list of
possible completions. In this case, it would be something like:

'LATIN CAPITAL LETTER A',
'LATIN CAPITAL LETTER B',
'LATIN CAPITAL LETTER C',
'LATIN CAPITAL LETTER D',
....

This help to type unicode character that do not have short latex aliases, and
have long unicode names. for example ``Ͱ``, ``\GREEK CAPITAL LETTER HETA``.

This feature was contributed by Luciana Marques `ghpull:`#11583`.
