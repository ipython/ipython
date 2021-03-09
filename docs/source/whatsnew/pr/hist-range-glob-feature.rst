History Range Glob feature
==========================

Previously, when using ``%history`` users could specify either
a range of sessions and lines, for example:

``~8/1-~6/5`` see history from the first line of 8 sessions ago,
              to the fifth line of 6 sessions ago.

Or users could specify ``-g <pattern>`` to glob ALL history for
the specified pattern.

However users could **\ *not*\ ** specify both.
If a user did specify both a range, and a glob pattern,
then the glob pattern would be used *but the range would be ignored*.

With this enhancment, if a user specifies both a range and a glob pattern,
the glob pattern will be applied to the specified range of history.
