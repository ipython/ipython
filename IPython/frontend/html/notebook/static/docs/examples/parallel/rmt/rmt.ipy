# <nbformat>2</nbformat>

# <markdowncell>

# # Eigenvalue distribution of Gaussian orthogonal random matrices

# <markdowncell>

# The eigenvalues of random matrices obey certain statistical laws. Here we construct random matrices
# from the Gaussian Orthogonal Ensemble (GOE), find their eigenvalues and then investigate the nearest
# neighbor eigenvalue distribution $\rho(s)$.

# <codecell>

from rmtkernel import ensemble_diffs, normalize_diffs, GOE
import numpy as np
from IPython.parallel import Client

# <markdowncell>

# ## Wigner's nearest neighbor eigenvalue distribution

# <markdowncell>

# The Wigner distribution gives the theoretical result for the nearest neighbor eigenvalue distribution
# for the GOE:
#
# $$\rho(s) = \frac{\pi s}{2} \exp(-\pi s^2/4)$$

# <codecell>

def wigner_dist(s):
    """Returns (s, rho(s)) for the Wigner GOE distribution."""
    return (np.pi*s/2.0) * np.exp(-np.pi*s**2/4.)

# <codecell>

def generate_wigner_data():
    s = np.linspace(0.0,4.0,400)
    rhos = wigner_dist(s)
    return s, rhos

# <codecell>

s, rhos = generate_wigner_data()

# <codecell>

plot(s, rhos)
xlabel('Normalized level spacing s')
ylabel('Probability $\rho(s)$')

# <markdowncell>

# ## Serial calculation of nearest neighbor eigenvalue distribution

# <markdowncell>

# In this section we numerically construct and diagonalize a large number of GOE random matrices
# and compute the nerest neighbor eigenvalue distribution. This comptation is done on a single core.

# <codecell>

def serial_diffs(num, N):
    """Compute the nearest neighbor distribution for num NxX matrices."""
    diffs = ensemble_diffs(num, N)
    normalized_diffs = normalize_diffs(diffs)
    return normalized_diffs

# <codecell>

serial_nmats = 1000
serial_matsize = 50

# <codecell>

%timeit -r1 -n1 serial_diffs(serial_nmats, serial_matsize)

# <codecell>

serial_diffs = serial_diffs(serial_nmats, serial_matsize)

# <markdowncell>

# The numerical computation agrees with the predictions of Wigner, but it would be nice to get more
# statistics. For that we will do a parallel computation.

# <codecell>

hist_data = hist(serial_diffs, bins=30, normed=True)
plot(s, rhos)
xlabel('Normalized level spacing s')
ylabel('Probability $P(s)$')

# <markdowncell>

# ## Parallel calculation of nearest neighbor eigenvalue distribution

# <markdowncell>

# Here we perform a parallel computation, where each process constructs and diagonalizes a subset of
# the overall set of random matrices.

# <codecell>

def parallel_diffs(rc, num, N):
    nengines = len(rc.targets)
    num_per_engine = num/nengines
    print "Running with", num_per_engine, "per engine."
    ar = rc.apply_async(ensemble_diffs, num_per_engine, N)
    diffs = np.array(ar.get()).flatten()
    normalized_diffs = normalize_diffs(diffs)
    return normalized_diffs

# <codecell>

client = Client()
view = client[:]
view.run('rmtkernel.py')
view.block = False

# <codecell>

parallel_nmats = 40*serial_nmats
parallel_matsize = 50

# <codecell>

%timeit -r1 -n1 parallel_diffs(view, parallel_nmats, parallel_matsize)

# <codecell>

pdiffs = parallel_diffs(view, parallel_nmats, parallel_matsize)

# <markdowncell>

# Again, the agreement with the Wigner distribution is excellent, but now we have better
# statistics.

# <codecell>

hist_data = hist(pdiffs, bins=30, normed=True)
plot(s, rhos)
xlabel('Normalized level spacing s')
ylabel('Probability $P(s)$')

