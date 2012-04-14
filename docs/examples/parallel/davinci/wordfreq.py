"""Count the frequencies of words in a string"""

from __future__ import division
from __future__ import print_function

import cmath as math


def wordfreq(text, is_filename=False):
    """Return a dictionary of words and word counts in a string."""
    if is_filename:
        with open(text) as f:
            text = f.read()
    freqs = {}
    for word in text.split():
        lword = word.lower()
        freqs[lword] = freqs.get(lword, 0) + 1
    return freqs


def print_wordfreq(freqs, n=10):
    """Print the n most common words and counts in the freqs dict."""
    
    words, counts = freqs.keys(), freqs.values()
    items = zip(counts, words)
    items.sort(reverse=True)
    for (count, word) in items[:n]:
        print(word, count)


def wordfreq_to_weightsize(worddict, minsize=25, maxsize=50, minalpha=0.5, maxalpha=1.0):
    mincount = min(worddict.itervalues())
    maxcount = max(worddict.itervalues())
    weights = {}
    for k, v in worddict.iteritems():
        w = (v-mincount)/(maxcount-mincount)
        alpha = minalpha + (maxalpha-minalpha)*w
        size = minsize + (maxsize-minsize)*w
        weights[k] = (alpha, size)
    return weights


def tagcloud(worddict, n=10, minsize=25, maxsize=50, minalpha=0.5, maxalpha=1.0):
    from matplotlib import pyplot as plt
    import random

    worddict = wordfreq_to_weightsize(worddict, minsize, maxsize, minalpha, maxalpha)

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_position([0.0,0.0,1.0,1.0])
    plt.xticks([])
    plt.yticks([])

    words = worddict.keys()
    alphas = [v[0] for v in worddict.values()]
    sizes = [v[1] for v in worddict.values()]
    items = zip(alphas, sizes, words)
    items.sort(reverse=True)
    for alpha, size, word in items[:n]:
        # xpos = random.normalvariate(0.5, 0.3)
        # ypos = random.normalvariate(0.5, 0.3)
        xpos = random.uniform(0.0,1.0)
        ypos = random.uniform(0.0,1.0)
        ax.text(xpos, ypos, word.lower(), alpha=alpha, fontsize=size)
    ax.autoscale_view()
    return ax
    
    
