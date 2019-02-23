Unicode name completions
========================

The #11583 Pull Request provides IPython a new feature. Previously, we provided completion for a unicode name with its relative symbol. With this, now IPython provides complete suggestions to unicode name symbols. As on the PR, if user types '\LAT<tab>', IPython provides a list of possible completions. In this case, it would be something like: 'LATIN CAPITAL LETTER A', 'LATIN CAPITAL LETTER B', 'LATIN CAPITAL LETTER C', etc.