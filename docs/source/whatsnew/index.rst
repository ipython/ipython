.. Developers should add in this file, during each release cycle, information
.. about important changes they've made, in a summary format that's meant for
.. end users.  For each release we normally have three sections: features,  bug
.. fixes and api breakage.
.. Please remember to credit the authors of the contributions by name,
.. especially when they are new users or developers who do not regularly
.. participate  in IPython's development.

.. _whatsnew_index:

=====================
What's new in IPython
=====================

..
    this will appear in the docs if we are not releasing a version (ie if
    `_version_extra` in release.py is an empty string)

.. only:: ipydev

   Development version in-progress features:
   
   .. toctree::

      development


This section documents the changes that have been made in various versions of
IPython. Users should consult these pages to learn about new features, bug
fixes and backwards incompatibilities. Developers should summarize the
development work they do here in a user friendly format.

.. toctree::
   :maxdepth: 1

   version9
   version8
   github-stats-8
   version7
   github-stats-7
   version6
   github-stats-6
   version5
   github-stats-5
   version4
   github-stats-4
   version3
   github-stats-3
   version3_widget_migration
   version2.0
   github-stats-2.0
   version1.0
   github-stats-1.0
   version0.13
   github-stats-0.13
   version0.12
   github-stats-0.12
   version0.11
   github-stats-0.11
   version0.10
   version0.9
   version0.8

..
   this makes a hidden toctree that keeps sphinx from complaining about
   documents included nowhere when building docs for stable
   We place it at the end as it will still be reachable via prev/next links.
   
.. only:: ipystable

   .. toctree::
      :hidden:

      development
