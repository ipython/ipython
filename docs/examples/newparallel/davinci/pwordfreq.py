#!/usr/bin/env python
"""Parallel word frequency counter.

This only works for a local cluster, because the filenames are local paths.
"""


import os
import time
import urllib

from itertools import repeat

from wordfreq import print_wordfreq, wordfreq

from IPython.parallel import Client, Reference

davinci_url = "http://www.gutenberg.org/cache/epub/5000/pg5000.txt"

def pwordfreq(view, fnames):
    """Parallel word frequency counter.
    
    view - An IPython DirectView
    fnames - The filenames containing the split data.
    """
    assert len(fnames) == len(view.targets)
    view.scatter('fname', fnames, flatten=True)
    ar = view.apply(wordfreq, Reference('fname'))
    freqs_list = ar.get()
    word_set = set()
    for f in freqs_list:
        word_set.update(f.keys())
    freqs = dict(zip(word_set, repeat(0)))
    for f in freqs_list:
        for word, count in f.iteritems():
            freqs[word] += count
    return freqs

if __name__ == '__main__':
    # Create a Client and View
    rc = Client()
    
    view = rc[:]

    if not os.path.exists('davinci.txt'):
        # download from project gutenberg
        print "Downloading Da Vinci's notebooks from Project Gutenberg"
        urllib.urlretrieve(davinci_url, 'davinci.txt')
        
    # Run the serial version
    print "Serial word frequency count:"
    text = open('davinci.txt').read()
    tic = time.time()
    freqs = wordfreq(text)
    toc = time.time()
    print_wordfreq(freqs, 10)
    print "Took %.3f s to calcluate"%(toc-tic)
    
    
    # The parallel version
    print "\nParallel word frequency count:"
    # split the davinci.txt into one file per engine:
    lines = text.splitlines()
    nlines = len(lines)
    n = len(rc)
    block = nlines/n
    for i in range(n):
        chunk = lines[i*block:i*(block+1)]
        with open('davinci%i.txt'%i, 'w') as f:
            f.write('\n'.join(chunk))
    
    cwd = os.path.abspath(os.getcwdu())
    fnames = [ os.path.join(cwd, 'davinci%i.txt'%i) for i in range(n)]
    tic = time.time()
    pfreqs = pwordfreq(view,fnames)
    toc = time.time()
    print_wordfreq(freqs)
    print "Took %.3f s to calcluate on %i engines"%(toc-tic, len(view.targets))
    # cleanup split files
    map(os.remove, fnames)
