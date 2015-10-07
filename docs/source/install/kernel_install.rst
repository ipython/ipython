.. _kernel_install:

Installing the IPython kernel
=============================

IPython can be installed (different python versions, virtualenv or conda
environments) as a kernel for Jupyter by following these steps:

* make sure that the desired python installation is active
  (e.g. activate the environment, or use absolute paths)
  and ipykernel is installed
* run once ``ipython kernel install --user``,
  or ``python -m ipykernel install --user`` to ensure a specific Python installation is used.


The last command installs a :ref:`kernel spec <jupyterclient:kernelspecs>` file for the current python installation. Kernel spec files are JSON files, which can be viewed and changed with a
normal text editor.

For example:

.. sourcecode:: bash

    source activate kernel-environment
    ipython kernel install --user
    source deactivate kernel-environment

or

.. sourcecode:: bash

    ~/envs/kernel-environment/python -m ipykernel install --user


.. _multiple_kernel_install:

Multiple IPython installs
=========================

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

