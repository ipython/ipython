Unicode Completion update
-------------------------

In IPython 7.1 the unicode completion map has been updated and synchronized with
the Julia language.

Added and removed character characters:

 ``\jmath`` (``ȷ``), ``\\underleftrightarrow`` (U+034D, combining) have been
 added, while ``\\textasciicaron`` have been removed

Some sequence have seen their prefix removed:

 - 6 characters ``\text...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 45 characters ``\Elz...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 65 characters ``\B...<tab>`` should now be inputed with ``\...<tab>`` directly,
 - 450 characters ``\m...<tab>`` should now be inputed with ``\...<tab>`` directly,

Some sequence have seen their prefix shortened:

 - 5 characters ``\mitBbb...<tab>`` should now be inputed with ``\bbi...<tab>`` directly,
 - 52 characters ``\mit...<tab>`` should now be inputed with ``\i...<tab>`` directly,
 - 216 characters ``\mbfit...<tab>`` should now be inputed with ``\bi...<tab>`` directly,
 - 222 characters ``\mbf...<tab>`` should now be inputed with ``\b...<tab>`` directly,

A couple of character had their sequence simplified:

 - ``ð``, type ``\dh<tab>``, instead of ``\eth<tab>``
 - ``ħ``, type ``\hbar<tab>``, instead of ``\Elzxh<tab>``
 - ``ɸ``, type ``\ltphi<tab>``, instead of ``\textphi<tab>``
 - ``ϴ``, type ``\varTheta<tab>``, instead of ``\textTheta<tab>``
 - ``ℇ``, type ``\eulermascheroni<tab>``, instead of ``\Eulerconst<tab>``
 - ``ℎ``, type ``\planck<tab>``, instead of ``\Planckconst<tab>``

 - U+0336 (COMBINING LONG STROKE OVERLAY), type ``\strike<tab>``, instead of ``\Elzbar<tab>``.

A couple of sequences have been updated:

 - ``\varepsilon`` now give ``ɛ`` (GREEK SMALL LETTER EPSILON) instead of ``ε`` (GREEK LUNATE EPSILON SYMBOL),
 - ``\underbar`` now give U+0331 (COMBINING MACRON BELOW) instead of U+0332 (COMBINING LOW LINE).

