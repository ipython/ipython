.. _following-latest:

=============================
 Following the latest source
=============================

These are the instructions if you just want to follow the latest
*ipython* source, but you don't need to do any development for now.

The steps are:

* :ref:`install-git`
* get local copy of the git repository from github_
* update local copy from time to time

Get the local copy of the code
==============================

From the command line::

   git clone git://github.com/ipython/ipython.git

You now have a copy of the code tree in the new ``ipython`` directory.

Updating the code
=================

From time to time you may want to pull down the latest code.  Do this with::

   cd ipython
   git pull

The tree in ``ipython`` will now have the latest changes from the initial
repository.

.. include:: git_links.txt
