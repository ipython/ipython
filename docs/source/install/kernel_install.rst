.. _kernel_install:

Kernel Installation
-------------------

IPython can be installed (different python versions, virtualenv or conda 
environments) as a kernel by following these steps:

* make sure that the desired python installation is active (e.g. activate the environment)
  and ipython is installed
* run once ``ipython kernelspec install-self --user`` (or ``ipython2 ...`` or ``ipython3 ...``
  if you want to install specific python versions)

The last command installs a :ref:`kernel spec <jupyterclient:kernelspecs>` file for the current python installation. Kernel spec files are JSON files, which can be viewed and changed with a
normal text editor.
