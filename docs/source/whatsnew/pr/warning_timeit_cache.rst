Using %timeit prints warnings if there is atleast a 4x difference in timings
between the slowest and fastest runs, since this might meant that the multiple
runs are not independent of one another.