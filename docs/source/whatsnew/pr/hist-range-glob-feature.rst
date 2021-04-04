History Range Glob feature
==========================

Previously, when using ``%history``, users could specify either
a range of sessions and lines, for example:

.. code-block:: python

   ~8/1-~6/5   # see history from the first line of 8 sessions ago,
               # to the fifth line of 6 sessions ago.``

Or users could specify a glob pattern:

.. code-block:: python

   -g <pattern>  # glob ALL history for the specified pattern.

However users could *not* specify both.  

If a user *did* specify both a range and a glob pattern,
then the glob pattern would be used (globbing *all* history) *and the range would be ignored*.

---

With this enhancment, if a user specifies both a range and a glob pattern, then the glob pattern will be applied to the specified range of history.
