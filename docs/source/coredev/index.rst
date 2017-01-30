.. _core_developer_guide:

=================================
Guide for IPython core Developers
=================================

This guide documents the development of IPython itself.  Alternatively,
developers of third party tools and libraries that use IPython should see the
:doc:`../development/index`.


For instructions on how to make a developer install see :ref:`devinstall`.

.. toctree::
   :maxdepth: 1

   release_process


Backporting Pull requests
-------------------------

All pull requests should usually be made against ``master``, if a Pull Request
need to be backported to an earlier release; then it should be tagged with the
correct ``milestone``.

If you are an admin on the IPython repository just mention the **backport bot** to
do the work for you. The bot is evolving so instructions may be different. At
the time of this writing you can use::

    @meeseeksdev[bot] backport to <branchname>

The bot will attempt to backport the current pull-request and issue a PR if
possible.

.. note::

    The ``@`` and ``[dev]`` when mentioning the bot should be optional and can
    be omitted.


Backport with ghpro
-------------------

We can also use `ghpro <https://pypi.python.org/pypi/ghpro>`
to automatically list and apply the PR on other branches. For example:

.. code-block:: bash
    
    $ backport-pr todo --milestone 5.2
    [...snip..]
    The following PRs have been backported
    9848
    9851
    9953
    9955
    The following PRs should be backported:
    9417
    9863
    9925
    9947

    $ backport-pr apply 5.x 9947
    [...snip...]


Old Documentation
=================

Out of date documentation is still available and have been kept for archival purposes.

.. note::

  Developers documentation used to be on the IPython wiki, but are now out of
  date. The wiki is though still available for historical reasons: `Old IPython
  GitHub Wiki.  <https://github.com/ipython/ipython/wiki/Dev:-Index>`_
