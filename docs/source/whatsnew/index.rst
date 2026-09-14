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
      :maxdepth: 1

      development


This section documents the changes that have been made in various versions of
IPython. Users should consult these pages to learn about new features, bug
fixes and backwards incompatibilities. Developers should summarize the
development work they do here in a user friendly format.

.. toctree::
   :maxdepth: 1

   version9
   version8
   version7
   version6
   version5
   version4
   version3
   version3_widget_migration
   version2.0
   version1.0
   version0.13
   version0.12
   version0.11
   version0.10
   version0.9
   version0.8

..
   The development.rst is included in the ipydev toctree above.
   For stable builds, it's automatically excluded by the only directive,
   so no hidden toctree is needed here.
