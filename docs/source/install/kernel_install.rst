.. _kernel_install:

Installing the IPython kernel
=============================

.. seealso::

   :ref:`Installing Jupyter <jupyter:install>`
     The IPython kernel is the Python execution backend for Jupyter.

The Jupyter Notebook and other frontends automatically ensure that the IPython kernel is available.
However, if you want to use a kernel with a different version of Python, or in a virtualenv or conda environment,
you'll need to install that manually.

Kernels for Python 2 and 3
--------------------------

If you're running Jupyter on Python 3, you can set up a Python 2 kernel after
checking your version of pip is greater than 9.0::

    python2 -m pip --version

Then install with ::

    python2 -m pip install ipykernel
    python2 -m ipykernel install --user

Or using conda, create a Python 2 environment::

    conda create -n ipykernel_py2 python=2 ipykernel
    source activate ipykernel_py2    # On Windows, remove the word 'source'
    python -m ipykernel install --user

.. note::

    IPython 6.0 stopped support for Python 2, so
    installing IPython on Python 2 will give you an older version (5.x series).

If you're running Jupyter on Python 2 and want to set up a Python 3 kernel,
follow the same steps, replacing ``2`` with ``3``.

The last command installs a :ref:`kernel spec <jupyterclient:kernelspecs>` file
for the current python installation. Kernel spec files are JSON files, which
can be viewed and changed with a normal text editor.

.. _multiple_kernel_install:

Kernels for different environments
----------------------------------

If you want to have multiple IPython kernels for different virtualenvs or conda
environments, you will need to specify unique names for the kernelspecs.

Make sure you have ipykernel installed in your environment. If you are using
``pip`` to install ``ipykernel`` in a conda env, make sure ``pip`` is
installed:

.. sourcecode:: bash

    source activate myenv
    conda install pip
    conda install ipykernel # or pip install ipykernel

For example, using conda environments, install a ``Python (myenv)`` Kernel in a first
environment:

.. sourcecode:: bash

    source activate myenv
    python -m ipykernel install --user --name myenv --display-name "Python (myenv)"

And in a second environment, after making sure ipykernel is installed in it:

.. sourcecode:: bash

    source activate other-env
    python -m ipykernel install --user --name other-env --display-name "Python (other-env)"

The ``--name`` value is used by Jupyter internally. These commands will overwrite
any existing kernel with the same name. ``--display-name`` is what you see in
the notebook menus.

Using virtualenv or conda envs, you can make your IPython kernel in one env available to Jupyter in a different env. To do so, run ipykernel install from the kernel's env, with --prefix pointing to the Jupyter env:

.. sourcecode:: bash

    /path/to/kernel/env/bin/python -m ipykernel install --prefix=/path/to/jupyter/env --name 'python-my-env'

Note that this command will create a new configuration for the kernel in one of the preferred location (see ``jupyter --paths`` command for more details):

* system-wide (e.g. /usr/local/share),
* in Jupyter's env (sys.prefix/share),
* per-user (~/.local/share or ~/Library/share)

If you want to edit the kernelspec before installing it, you can do so in two steps.
First, ask IPython to write its spec to a temporary location:

.. sourcecode:: bash

    ipython kernel install --prefix /tmp

edit the files in /tmp/share/jupyter/kernels/python3 to your liking, then when you are ready, tell Jupyter to install it (this will copy the files into a place Jupyter will look):

.. sourcecode:: bash

    jupyter kernelspec install /tmp/share/jupyter/kernels/python3
