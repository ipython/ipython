"""Compute statistics on the digits of pi.

This uses precomputed digits of pi from the website
of Professor Yasumasa Kanada at the University of
Tokoyo: http://www.super-computing.org/

Currently, there are only functions to read the
.txt (non-compressed, non-binary) files, but adding
support for compression and binary files would be
straightforward.

This focuses on computing the number of times that
all 1, 2, n digits sequences occur in the digits of pi.
If the digits of pi are truly random, these frequencies
should be equal.
"""

# Import statements
from __future__ import division, with_statement

import numpy as np
from matplotlib import pyplot as plt

try : #python2
    from urllib import urlretrieve
except ImportError : #python3
    from urllib.request import urlretrieve

	# Top-level functions

def fetch_pi_file(filename):
    """This will download a segment of pi from super-computing.org
    if the file is not already present.
    """
    import os, urllib
    ftpdir="ftp://pi.super-computing.org/.2/pi200m/"
    if os.path.exists(filename):
        # we already have it
        return
    else:
        # download it
        urlretrieve(ftpdir+filename,filename)

def compute_one_digit_freqs(filename):
    """
    Read digits of pi from a file and compute the 1 digit frequencies.
    """
    d = txt_file_to_digits(filename)
    freqs = one_digit_freqs(d)
    return freqs

def compute_two_digit_freqs(filename):
    """
    Read digits of pi from a file and compute the 2 digit frequencies.
    """
    d = txt_file_to_digits(filename)
    freqs = two_digit_freqs(d)
    return freqs

def reduce_freqs(freqlist):
    """
    Add up a list of freq counts to get the total counts.
    """
    allfreqs = np.zeros_like(freqlist[0])
    for f in freqlist:
        allfreqs += f
    return allfreqs

def compute_n_digit_freqs(filename, n):
    """
    Read digits of pi from a file and compute the n digit frequencies.
    """
    d = txt_file_to_digits(filename)
    freqs = n_digit_freqs(d, n)
    return freqs

# Read digits from a txt file

def txt_file_to_digits(filename, the_type=str):
    """
    Yield the digits of pi read from a .txt file.
    """
    with open(filename, 'r') as f:
        for line in f.readlines():
            for c in line:
                if c != '\n' and c!= ' ':
                    yield the_type(c)

# Actual counting functions

def one_digit_freqs(digits, normalize=False):
    """
    Consume digits of pi and compute 1 digit freq. counts.
    """
    freqs = np.zeros(10, dtype='i4')
    for d in digits:
        freqs[int(d)] += 1
    if normalize:
        freqs = freqs/freqs.sum()
    return freqs

def two_digit_freqs(digits, normalize=False):
    """
    Consume digits of pi and compute 2 digits freq. counts.
    """
    freqs = np.zeros(100, dtype='i4')
    last = next(digits)
    this = next(digits)
    for d in digits:
        index = int(last + this)
        freqs[index] += 1
        last = this
        this = d
    if normalize:
        freqs = freqs/freqs.sum()
    return freqs

def n_digit_freqs(digits, n, normalize=False):
    """
    Consume digits of pi and compute n digits freq. counts.

    This should only be used for 1-6 digits.
    """
    freqs = np.zeros(pow(10,n), dtype='i4')
    current = np.zeros(n, dtype=int)
    for i in range(n):
        current[i] = next(digits)
    for d in digits:
        index = int(''.join(map(str, current)))
        freqs[index] += 1
        current[0:-1] = current[1:]
        current[-1] = d
    if normalize:
        freqs = freqs/freqs.sum()
    return freqs

# Plotting functions

def plot_two_digit_freqs(f2):
    """
    Plot two digits frequency counts using matplotlib.
    """
    f2_copy = f2.copy()
    f2_copy.shape = (10,10)
    ax = plt.matshow(f2_copy)
    plt.colorbar()
    for i in range(10):
        for j in range(10):
            plt.text(i-0.2, j+0.2, str(j)+str(i))
    plt.ylabel('First digit')
    plt.xlabel('Second digit')
    return ax

def plot_one_digit_freqs(f1):
    """
    Plot one digit frequency counts using matplotlib.
    """
    ax = plt.plot(f1,'bo-')
    plt.title('Single digit counts in pi')
    plt.xlabel('Digit')
    plt.ylabel('Count')
    return ax
