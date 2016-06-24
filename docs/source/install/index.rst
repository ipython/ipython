.. _install_index:

============
Installation
============

.. toctree::
   :maxdepth: 3
   :hidden:


   install
   kernel_install



This sections will guide you into `installing IPython itself <install>`_, and
installing `kernels for jupyter <kernel_install>`_ if you are working with
multiple version of Python, or multiple environments. 

To know more, head to the next section. 


Quick install reminder
~~~~~~~~~~~~~~~~~~~~~~

Here is a quick reminder of the various commands needed if you are already
familiar with IPython and are just searching to refresh your memory:

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

   `Installing Jupyter <http://jupyter.readthedocs.io/en/latest/install.html>`__
     The Notebook, nbconvert, and many other former pieces of IPython are now
     part of Project Jupyter.


