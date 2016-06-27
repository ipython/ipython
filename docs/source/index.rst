.. _introduction:

=====================
IPython Documentation
=====================

.. htmlonly::

   :Release: |release|
   :Date: |today|

Welcome to the official IPython documentation

IPython provides a rich toolkit to help you make the most out of using Python
interactively.  Its main components are:

* A powerful interactive Python shell

* A `Jupyter <http://jupyter.org/>`_ kernel to work with Python code in Jupyter
  notebooks and other interactive frontends.

The enhanced interactive Python shells and kernel have the following main
features:

* Comprehensive object introspection.

* Input history, persistent across sessions.

* Caching of output results during a session with automatically generated
  references.

* Extensible tab completion, with support by default for completion of python
  variables and keywords, filenames and function keywords.

* Extensible system of 'magic' commands for controlling the environment and
  performing many tasks related either to IPython or the operating system.

* A rich configuration system with easy switching between different setups
  (simpler than changing $PYTHONSTARTUP environment variables every time).

* Session logging and reloading.

* Extensible syntax processing for special purpose situations.

* Access to the system shell with user-extensible alias system.

* Easily embeddable in other Python programs and GUIs.

* Integrated access to the pdb debugger and the Python profiler.


The Command line interface inherit all the above functionality and posses 
 
* real multi-line editing.
 
* syntax highlighting as you type

* integration with command line editor for a better workflow.

The kernel also have its share of feature, when used with a compatible frontend
it allows for:

* rich display system for object allowing to display Html, Images, Latex,Sounds
  Video.

* interactive widgets with the use of the ``ipywidgets`` package.


This documentation will walk through most of the features of the IPython
command line and kernel, as well as describe the internals mechanisms in order
to improve your Python workflow.

You can always find the table of content for this documentation in the left
sidebar, allowing you to come back on previous section if needed, or skip ahead. 


The latest development version is always available from IPython's `GitHub
repository <http://github.com/ipython/ipython>`_.




.. toctree::
   :maxdepth: 1
   :hidden:

   self
   overview
   whatsnew/index
   install/index
   interactive/index
   config/index
   development/index
   coredev/index
   api/index
   about/index

.. seealso::

   `Jupyter documentation <http://jupyter.readthedocs.io/en/latest/>`__
     The Notebook code and many other pieces formerly in IPython are now parts
     of Project Jupyter.
   `ipyparallel documentation <http://ipyparallel.readthedocs.io/en/latest/>`__
     Formerly ``IPython.parallel``.


.. htmlonly::
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

