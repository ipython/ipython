"""Count the frequencies of words in a string"""

def wordfreq(text):
    """Return a dictionary of words and word counts in a string."""

    freqs = {}
    for word in text.split():
        freqs[word] = freqs.get(word, 0) + 1
    return freqs

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