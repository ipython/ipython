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

If you're running Jupyter on Python 3, you can set up a Python 2 kernel like this::

    python2 -m pip install ipykernel
    python2 -m ipykernel install --user

Or using conda, create a Python 2 environment::

    conda create -n ipykernel_py2 python=2 ipykernel
    source activate ipykernel_py2    # On Windows, remove the word 'source'
    python -m ipykernel install --user

If you're running Jupyter on Python 2 and want to set up a Python 3 kernel,
follow the same steps, replacing ``2`` with ``3``.

The last command installs a :ref:`kernel spec <jupyterclient:kernelspecs>` file
for the current python installation. Kernel spec files are JSON files, which
can be viewed and changed with a normal text editor.

.. _multiple_kernel_install:

Kernels for different environments
----------------------------------

If you want to have multiple IPython kernels for different virtualenvs or conda environments,
you will need to specify unique names for the kernelspecs.

For example, using conda environments:

.. sourcecode:: bash

    source activate myenv
    python -m ipykernel install --user --name myenv --display-name "Python (myenv)"
    source activate other-env
    python -m ipykernel install --user --name other-env --display-name "Python (other-env)"

The ``--name`` value is used by Jupyter internally. These commands will overwrite
any existing kernel with the same name. ``--display-name`` is what you see in
the notebook menus.

Using virtualenv you can add your new environments by linking to specific instance of your Python:

.. sourcecode:: bash

    python -m ipykernel install --prefix=/path/to/new_env --name python_new_env
  
Note that this command will create new configuration for kernel in one of it's prefered location (see ``jupyter --paths`` command for more details):

* system-wide (e.g. /usr/local/share),
* in Jupyter's env (sys.prefix/share),
* per-user (~/.local/share or ~/Library/share)

You can also create configuration in temporary location and install it in Jupyter (copy configuration files) with:

.. sourcecode:: bash

    ipython kernel install --prefix /tmp
    jupyter kernelspec install /tmp/share/jupyter/kernels/python3

**Deprecated:** You can also create configuration for new environment by new configuration's file in `~/.ipython/kernels/my_env/kernel.json` with following content::

   {
      "argv": ["~/path/to/env/bin/python", "-m", "IPython.kernel",
         "-f", "{connection_file}"],
      "display_name": "Python 3 (my new env)",
      "language": "python"
   }

Please note that kernel detection in standard ``~/.ipython/`` location is supported as part of backward-compatibility and may not be provided in further versions.
