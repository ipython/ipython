"""Count the frequencies of words in a string"""

def wordfreq(text):
    """Return a dictionary of words and word counts in a string."""


def print_wordfreq(freqs, n=10):
    """Print the n most common words and counts in the freqs dict."""
    words, counts = freqs.keys(), freqs.values()
    items = zip(counts, words)
    items.sort(reverse=True)
    for (count, word) in items[:n]:
        print word, count

if __name__ == '__main__':
    import gzip
    text = gzip.open('HISTORY.gz').read()
    freqs = wordfreq(text)