.. _install:

Installing IPython
==================


IPython 6 requires Python ≥ 3.3. IPython 5.x can be installed on Python 2.


Quick Install 
-------------

With ``pip`` already installed :

.. code-block:: bash

    $ pip install ipython

This installs IPython as well as its dependencies.

If you want to use IPython with notebooks or the Qt console, you should also
install Jupyter ``pip install jupyter``.



Overview
--------

This document describes in detail the steps required to install IPython. For a
few quick ways to get started with package managers or full Python
distributions, see `the install page <https://ipython.org/install.html>`_ of the
IPython website.

Please let us know if you have problems installing IPython or any of its
dependencies.

IPython and most dependencies should be installed via :command:`pip`.
In many scenarios, this is the simplest method of installing Python packages.
More information about :mod:`pip` can be found on
`its PyPI page <https://pip.pypa.io>`__.


More general information about installing Python packages can be found in
`Python's documentation <http://docs.python.org>`_.

.. _dependencies:

Dependencies
~~~~~~~~~~~~

IPython relies on a number of other Python packages. Installing using a package
manager like pip or conda will ensure the necessary packages are installed.
Manual installation without dependencies is possible, but not recommended.
The dependencies can be viewed with package manager commands,
such as :command:`pip show ipython` or :command:`conda info ipython`.


Installing IPython itself
~~~~~~~~~~~~~~~~~~~~~~~~~

IPython requires several dependencies to work correctly, it is not recommended
to install IPython and all its dependencies manually as this can be quite long
and troublesome. You should use the python package manager ``pip``.

Installation using pip
~~~~~~~~~~~~~~~~~~~~~~

Make sure you have the latest version of :mod:`pip` (the Python package
manager) installed. If you do not, head to `Pip documentation
<https://pip.pypa.io/en/stable/installing/>`_ and install :mod:`pip` first.

The quickest way to get up and running with IPython is to install it with pip:

.. code-block:: bash

    $ pip install ipython

That's it.


Installation from source
~~~~~~~~~~~~~~~~~~~~~~~~

To install IPython from source,
grab the latest stable tarball of IPython `from PyPI
<https://pypi.python.org/pypi/ipython>`__.  Then do the following:

.. code-block:: bash

    tar -xzf ipython-5.1.0.tar.gz
    cd ipython-5.1.0
    # The [test] extra ensures test dependencies are installed too:
    pip install '.[test]'

Do not invoke ``setup.py`` directly as this can have undesirable consequences
for further upgrades. We do not recommend using ``easy_install`` either.

If you are installing to a location (like ``/usr/local``) that requires higher
permissions, you may need to run the last command with :command:`sudo`. You can
also install in user specific location by using the ``--user`` flag in
conjunction with pip.

To run IPython's test suite, use the :command:`pytest` command:

.. code-block:: bash

    $ pytest

.. _devinstall:

Installing the development version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is also possible to install the development version of IPython from our
`Git <http://git-scm.com/>`_ source code repository.  To do this you will
need to have Git installed on your system.  


Then do:

.. code-block:: bash

    $ git clone https://github.com/ipython/ipython.git
    $ cd ipython
    $ pip install -e '.[test]'

The :command:`pip install -e .` command allows users and developers to follow
the development branch as it changes by creating links in the right places and
installing the command line scripts to the appropriate locations.

Then, if you want to update your IPython at any time, do:

.. code-block:: bash

    $ git pull

If the dependencies or entrypoints have changed, you may have to run

.. code-block:: bash

    $ pip install -e .

again, but this is infrequent.
