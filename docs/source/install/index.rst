.. _install_index:

============
Installation
============

.. toctree::
   :maxdepth: 3
   :hidden:


   install
   kernel_install



This sections will guide you through :ref:`installing IPython itself <install>`, and
installing :ref:`kernels for Jupyter <kernel_install>` if you wish to work with
multiple version of Python, or multiple environments.


Quick install reminder
~~~~~~~~~~~~~~~~~~~~~~

Here is a quick reminder of the commands needed for installation if you are
already familiar with IPython and are just searching to refresh your memory:

Install IPython:

.. code-block:: bash

    $ pip install ipython


Install and register an IPython kernel with Jupyter:


.. code-block:: bash

    $ python -m pip install ipykernel

    $ python -m ipykernel install [--user] [--name <machine-readable-name>] [--display-name <"User Friendly Name">]

for more help see 

.. code-block:: bash
    
    $ python -m ipykernel install  --help
    


.. seealso::

   `Installing Jupyter <https://jupyter.readthedocs.io/en/latest/install.html>`__
     The Notebook, nbconvert, and many other former pieces of IPython are now
     part of Project Jupyter.


