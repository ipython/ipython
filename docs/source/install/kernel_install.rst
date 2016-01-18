.. _kernel_install:

Installing the IPython kernel
=============================

The Jupyter Notebook and other frontends automatically ensure that the IPython kernel is available.
However, if you want to use a kernel with a different version of Python, or in a virtualenv or conda environment,
you'll need to install that manually.

Using the Python version or environment for which you want to set up the kernel, run::

    pip install ipykernel  # or: conda install ipykernel
    python -m ipykernel install --user

The last command installs a :ref:`kernel spec <jupyterclient:kernelspecs>` file
for the current python installation. Kernel spec files are JSON files, which
can be viewed and changed with a normal text editor.

See `python -m ipykernel install --help` for the list of installation options like
naming the kernel, or non default install location.

.. _multiple_kernel_install:

Multiple IPython installations
==============================

If you want to have multiple IPython kernels for different environments,
you will need to specify unique names for the kernelspecs,
and you may also want to specify the display name of those kernels,
so that you can clearly see which is which in the notebook menus:

.. sourcecode:: bash

    source activate myenv
    ipython kernel install --user --name myenv --display-name "Python (myenv)"
    source activate other-env
    ipython kernel install --user --name other-env --display-name "Python (other-env)"
    source deactivate

