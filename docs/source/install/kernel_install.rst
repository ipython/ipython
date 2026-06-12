.. _kernel_install:

Installing the IPython kernel
=============================

.. seealso::

   :ref:`Installing Jupyter <jupyter:install>`
     The IPython kernel is the Python execution backend for Jupyter.

The Jupyter Notebook and other frontends automatically ensure that the IPython kernel is available.
However, if you want to use a kernel with a different version of Python, or in a virtualenv or conda environment,
you'll need to install that manually.

Kernels for different Python versions
-------------------------------------

If you want a kernel for a different version of Python than the one Jupyter is
running on, install ``ipykernel`` using that Python and register it::

    /path/to/python -m pip install ipykernel
    /path/to/python -m ipykernel install --user

Or using conda, create an environment with the desired Python version::

    conda create -n py312 python=3.12 ipykernel
    conda activate py312
    python -m ipykernel install --user --name py312 --display-name "Python 3.12"

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

    conda activate myenv
    conda install pip
    conda install ipykernel # or pip install ipykernel

For example, using conda environments, install a ``Python (myenv)`` Kernel in a first
environment:

.. sourcecode:: bash

    conda activate myenv
    python -m ipykernel install --user --name myenv --display-name "Python (myenv)"

And in a second environment, after making sure ipykernel is installed in it:

.. sourcecode:: bash

    conda activate other-env
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
