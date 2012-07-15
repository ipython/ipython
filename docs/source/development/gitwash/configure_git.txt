.. _configure-git:

===============
 Configure git
===============

.. _git-config-basic:

Overview
========

::

  git config --global user.email you@yourdomain.example.com
  git config --global user.name "Your Name Comes Here"


In detail
=========

This is to tell git_ who you are, for labeling any changes you make to
the code.  The simplest way to do this is from the command line::

  git config --global user.email you@yourdomain.example.com
  git config --global user.name "Your Name Comes Here"

This will write the settings into your git configuration file - a file
called ``.gitconfig`` in your home directory. 

Advanced git configuration
==========================

You might well benefit from some aliases to common commands.

For example, you might well want to be able to shorten ``git checkout`` to ``git co``. 

The easiest way to do this, is to create a ``.gitconfig`` file in your
home directory, with contents like this::

  [core]
          editor = emacs
  [user]
          email = you@yourdomain.example.com
          name = Your Name Comes Here
  [alias]
          st = status
          stat = status
          co = checkout
  [color]
          diff = auto
          status = true

(of course you'll need to set your email and name, and may want to set
your editor).  If you prefer, you can do the same thing from the command
line::

  git config --global core.editor emacs
  git config --global user.email you@yourdomain.example.com
  git config --global user.name "Your Name Comes Here"
  git config --global alias.st status
  git config --global alias.stat status
  git config --global alias.co checkout
  git config --global color.diff auto
  git config --global color.status true

These commands will write to your user's git configuration file
``~/.gitconfig``.

To set up on another computer, you can copy your ``~/.gitconfig`` file,
or run the commands above.

Other configuration recommended by Yarik
========================================

In your ``~/.gitconfig`` file alias section::

   wdiff = diff --color-words

so that ``git wdiff`` gives a nicely formatted output of the diff. 

To enforce summaries when doing merges(``~/.gitconfig`` file again)::

   [merge]
      summary = true


.. include:: git_links.txt


