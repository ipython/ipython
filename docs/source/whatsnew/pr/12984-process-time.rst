windows time-implementation: Switch to process_time
===================================================
Timing for example with ``%%time`` on windows is based on ``time.perf_counter``.
This is at the end the same as W-All.
To be a bit tighter to linux one could change to ``time.process_time`` instead.
Thus for example one would no longer count periods of sleep and further.
