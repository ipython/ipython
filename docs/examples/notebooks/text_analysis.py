#!/usr/bin/env python
"""Simple text analysis: word frequencies and co-occurrence graph.

Usage:

  text_analysis.py [text_file]

This script will analize a plain text file treating it as a list of
newline-separated sentences (e.g. a list of paper titles).

It computes word frequencies (after doing some naive normalization by
lowercasing and throwing away a few overly common words).  It also computes,
from the most common words, a weighted graph of word co-occurrences and
displays it, as well as summarizing the graph structure by ranking its nodes in
descending order of eigenvector centrality.

This is meant as an illustration of text processing in Python, using matplotlib
for visualization and NetworkX for graph-theoretical manipulation.  It should
not be considered production-strength code for serious text analysis.

Author: Fernando Perez <fernando.perez@berkeley.edu>
"""

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

# From the standard library
import os
import re
import sys
import urllib2

# Third-party libraries
import networkx as nx
import numpy as np

from matplotlib import pyplot as plt

#-----------------------------------------------------------------------------
# Function definitions
#-----------------------------------------------------------------------------

def rescale_arr(arr,amin,amax):
    """Rescale an array to a new range.

    Return a new array whose range of values is (amin,amax).

    Parameters
    ----------
    arr : array-like

    amin : float
      new minimum value

    amax : float
      new maximum value

    Examples
    --------
    >>> a = np.arange(5)

    >>> rescale_arr(a,3,6)
    array([ 3.  ,  3.75,  4.5 ,  5.25,  6.  ])
    """
    
    # old bounds
    m = arr.min()
    M = arr.max()
    # scale/offset
    s = float(amax-amin)/(M-m)
    d = amin - s*m
    
    # Apply clip before returning to cut off possible overflows outside the
    # intended range due to roundoff error, so that we can absolutely guarantee
    # that on output, there are no values > amax or < amin.
    return np.clip(s*arr+d,amin,amax)


def all_pairs(items):
    """Make all unique pairs (order doesn't matter)"""
    pairs = []
    nitems = len(items)
    for i, wi in enumerate(items):
        for j in range(i+1, nitems):
            pairs.append((wi, items[j]))
    return pairs


def text_cleanup(text, min_length=3,
                 remove = set(['for', 'the', 'and', 'with'])):
    """Clean up a list of lowercase strings of text for simple analysis.

    Splits on whitespace, removes all 'words' less than `min_length` characters
    long, and those in the `remove` set.

    Returns a list of strings.
    """
    return [w for w in text.lower().split()
            if len(w)>=min_length and w not in remove]
    

def print_vk(lst):
    """Print a list of value/key pairs nicely formatted in key/value order."""

    # Find the longest key: remember, the list has value/key paris, so the key
    # is element [1], not [0]
    longest_key = max([len(word) for word, count in lst])
    # Make a format string out of it
    fmt = '%'+str(longest_key)+'s -> %s'
    # Do actual printing
    for k,v in lst:
        print fmt % (k,v)


def word_freq(text):
    """Return a dictionary of word frequencies for the given text.

    Input text should be given as an iterable of strings."""

    freqs = {}
    for word in text:
        freqs[word] = freqs.get(word, 0) + 1        
    return freqs


def sort_freqs(freqs):
    """Sort a word frequency histogram represented as a dictionary.

    Parameters
    ----------
    freqs : dict
      A dict with string keys and integer values.
    
    Return
    ------
    items : list
      A list of (count, word) pairs.
    """
    items = freqs.items()
    items.sort(key = lambda wc: wc[1])
    return items
    ## words,counts = freqs.keys(),freqs.values()
    ## # Sort by count
    ## items = zip(counts,words)
    ## items.sort()
    ## return items


def summarize_freq_hist(freqs, n=10):
    """Print a simple summary of a word frequencies dictionary.

    Paramters
    ---------
    freqs : dict or list
      Word frequencies, represented either as a dict of word->count, or as a
      list of count->word pairs.
    
    n : int
      The number of least/most frequent words to print.
    """

    items = sort_freqs(freqs) if isinstance(freqs, dict) else freqs
    print 'Number of unique words:',len(freqs)
    print
    print '%d least frequent words:' % n
    print_vk(items[:n])
    print
    print '%d most frequent words:' % n
    print_vk(items[-n:])


def get_text_from_url(url):
    """Given a url (local file path or remote url), read its contents.

    If it's a remote URL, it downloads the file and leaves it locally cached
    for future runs.  If the local matching file is found, no download is made.

    Returns
    -------
    text : string
      The contents of the file.
    """
    if url.startswith('http'):
        # remote file, fetch only if needed
        fname = os.path.split(url)[1]
        if os.path.isfile(fname):
            with open(fname, 'r') as f:
                text = f.read()
        else:
            with open(fname, 'w') as f:
                text = urllib2.urlopen(url).read()
                f.write(text)
    else:
        with open(url, 'r') as f:
            text = f.read()
    return text


def co_occurrences(lines, words):
    """Return histogram of co-occurrences of words in a list of lines.
    
    Parameters
    ----------
    lines : list
      A list of strings considered as 'sentences' to search for co-occurrences.

    words : list
      A list of words from which all unordered pairs will be constructed and
      searched for co-occurrences.
    """
    wpairs = all_pairs(words)
    
    # Now build histogram of co-occurrences
    co_occur = {}
    for w1, w2 in wpairs:
        rx = re.compile('%s .*%s|%s .*%s' % (w1, w2, w2, w1))
        co_occur[w1, w2] = sum([1 for line in lines if rx.search(line)])

    return co_occur


def co_occurrences_graph(word_hist, co_occur, cutoff=0):
    """Convert a word histogram with co-occurrences to a weighted graph.

    Edges are only added if the count is above cutoff.
    """
    g = nx.Graph()
    for word, count in word_hist:
        g.add_node(word, count=count)
    for (w1, w2), count in co_occur.iteritems():
        if count<=cutoff:
            continue
        g.add_edge(w1, w2, weight=count)
    return g


def plot_graph(wgraph, pos=None):
    """Conveniently summarize graph visually"""
    # Plot nodes with size according to count
    sizes = []
    degrees = []
    for n, d in wgraph.nodes_iter(data=True):
        sizes.append(d['count'])
        degrees.append(wgraph.degree(n))
    sizes = rescale_arr(np.array(sizes, dtype=float), 100, 1000)
        
    # Compute layout and label edges according to weight
    pos = nx.spring_layout(wgraph) if pos is None else pos
    labels = {}
    width = []
    for n1, n2, d in wgraph.edges_iter(data=True):
        w = d['weight']
        labels[n1, n2] = w
        width.append(w)

    # remap width to 1-10 range
    width = rescale_arr(np.array(width, dtype=float), 1, 15)
        
    # Create figure
    fig = plt.figure()
    ax = fig.add_subplot(111)
    fig.subplots_adjust(0,0,1)
    nx.draw_networkx_nodes(wgraph, pos, node_size=sizes, node_color=degrees,
                           alpha=0.8)
    nx.draw_networkx_labels(wgraph, pos, font_size=15, font_weight='bold')
    nx.draw_networkx_edges(wgraph, pos, width=width, edge_color=width,
                           edge_cmap=plt.cm.Blues)
    nx.draw_networkx_edge_labels(wgraph, pos, edge_labels=labels)
    ax.set_title('Node color:degree, size:count, edge: co-occurrence count')


def plot_word_histogram(freqs, show=10, title=None):
    """Plot a histogram of word frequencies, limited to the top `show` ones.
    """
    sorted_f = sort_freqs(freqs) if isinstance(freqs, dict) else freqs

    # Don't show the tail
    if isinstance(show, int):
        # interpret as number of words to show in histogram
        show_f = sorted_f[-show:]
    else:
        # interpret as a fraction
        start = -int(round(show*len(freqs)))
        show_f = sorted_f[start:]
        
    # Now, extract words and counts, plot
    n_words = len(show_f)
    ind = np.arange(n_words)
    words = [i[0] for i in show_f]
    counts = [i[1] for i in show_f]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    if n_words<=20:
        # Only show bars and x labels for small histograms, they don't make
        # sense otherwise
        ax.bar(ind, counts)
        ax.set_xticks(ind)
        ax.set_xticklabels(words, rotation=45)
        fig.subplots_adjust(bottom=0.25)
    else:
        # For larger ones, do a step plot
        ax.step(ind, counts)

    # If it spans more than two decades, use a log scale
    if float(max(counts))/min(counts) > 100:
        ax.set_yscale('log')

    if title:
        ax.set_title(title)
    return ax


def summarize_centrality(centrality):
    c = centrality.items()
    c.sort(key=lambda x:x[1], reverse=True)
    print '\nGraph centrality'
    for node, cent in c:
        print "%15s: %.3g" % (node, cent)

#-----------------------------------------------------------------------------
# Main script
#-----------------------------------------------------------------------------

# if __name__ == '__main__':

    # # Configure user variables here
    #  # Specify the url (can be a local file path) of the text file to analyze.
    #  # If not given, it's read from the command line as the first argument
    # 
    #  # 11226 titles of recent articles in arxiv/math/prob
    #  default_url  = "http://bibserver.berkeley.edu/tmp/titles.txt"
    #  # Number of words to display in detailed histogram
    #  n_words = 15
    #  # Number of words to use as nodes for co-occurrence graph.
    #  n_nodes = 15
    # 
    #  # End of user configuration
    # 
    #  # Actual code starts here
    #  try:
    #      url = sys.argv[1]
    #  except IndexError:
    #      url  = default_url
    # 
    #  # Fetch text and do basic preprocessing
    #  text = get_text_from_url(url).lower()
    #  lines = text.splitlines()
    #  words = text_cleanup(text)
    # 
    #  # Compute frequency histogram
    #  wf = word_freq(words)
    #  sorted_wf = sort_freqs(wf)
    # 
    #  # Build a graph from the n_nodes most frequent words
    #  popular = sorted_wf[-n_nodes:]
    #  pop_words = [wc[0] for wc in popular]
    #  co_occur = co_occurrences(lines, pop_words)
    #  wgraph = co_occurrences_graph(popular, co_occur, cutoff=1)
    #  centrality = nx.eigenvector_centrality_numpy(wgraph)
    # 
    #  # Print summaries of single-word frequencies and graph structure
    #  summarize_freq_hist(sorted_wf)
    #  summarize_centrality(centrality)
    # 
    #  # Plot histogram and graph
    #  plt.close('all')
    #  plot_word_histogram(sorted_wf, n_words,
    #                      "Frequencies for %s most frequent words" % n_words)
    #  plot_word_histogram(sorted_wf, 1.0, "Frequencies for entire word list")
    #  plot_graph(wgraph)
    #      
    #  # Display figures
    #  plt.show()
