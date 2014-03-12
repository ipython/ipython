#-------------------------------------------------------------------------------
# Core routines for computing properties of symmetric random matrices.
#-------------------------------------------------------------------------------

import numpy as np
ra = np.random
la = np.linalg

def GOE(N):
    """Creates an NxN element of the Gaussian Orthogonal Ensemble"""
    m = ra.standard_normal((N,N))
    m += m.T
    return m/2


def center_eigenvalue_diff(mat):
    """Compute the eigvals of mat and then find the center eigval difference."""
    N = len(mat)
    evals = np.sort(la.eigvals(mat))
    diff = np.abs(evals[N/2] - evals[N/2-1])
    return diff


def ensemble_diffs(num, N):
    """Return num eigenvalue diffs for the NxN GOE ensemble."""
    diffs = np.empty(num)
    for i in xrange(num):
        mat = GOE(N)
        diffs[i] = center_eigenvalue_diff(mat)
    return diffs


def normalize_diffs(diffs):
    """Normalize an array of eigenvalue diffs."""
    return diffs/diffs.mean()


def normalized_ensemble_diffs(num, N):
    """Return num *normalized* eigenvalue diffs for the NxN GOE ensemble."""
    diffs = ensemble_diffs(num, N)
    return normalize_diffs(diffs)

