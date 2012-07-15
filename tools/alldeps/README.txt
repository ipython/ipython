===========================================================
 Self-contained IPython installation with all dependencies
===========================================================

This is a self-contained source distribution of IPython with all its
*non-graphical* dependencies, that installs in a single ``make`` call to your
home directory (by default) or any location of your choice.

This distribution is meant for developer-type usage in Unix environments, it is
*not* an easy way to get IPython working on Windows, since it assumes the
presence of a working compiler and development tools.

Currently, the distribution contains::

  ipython-0.9.1.tar.gz
  pyOpenSSL-0.6.tar.gz
  zope.interface-3.4.1.tar.gz
  Twisted-8.1.0.tar.bz2
  foolscap-0.3.1.tar.gz
  nose-0.10.3.tar.gz


Usage
=====

Download the single tarball where this README file lives and unpack it.  If
your system is already configured as described below, these lines will do the
whole job::

    wget http://ipython.scipy.org/dist/alldeps/ipython-alldeps-0.9.1.tar
    tar xf ipython-alldeps-0.9.1.tar
    cd ipython-alldeps-0.9.1
    make

If all goes well, then just type::

    iptest

to run IPython's test suite.

    
It is meant to be used in an environment where you have your ``$PATH``,
``$PYTHONPATH``, etc variables properly configured, so that the installation of
packages can be made with (using ``~/usr/local`` as an example)::

    python setup.py install --prefix=~/usr/local

For an explanation of how to do this, see below.

You can configure the default prefix used by editing the file
``pkginstall.cfg``, where you can also override the python version used for the
process.  If your system is configured in this manner, you can simply type::

    make

and this will build and install all of IPython's non-graphical dependencies on
your system, assuming you have Python, a compiler, the Python headers and the
SSL headers available.


.. _environment_configuration:

Environment configuration
=========================

Below is an example of what to put in your ``~/.bashrc`` file to configure your
environment as described in this document, in a reasonably portable manner that
takes 64-bit operating systems into account::

  # For processor dependent config
  MACHINE=$(uname -m)

  # Python version information
  PYVER=$(python -ESV 2>&1)
  PYVER_MINOR=${PYVER#Python }
  PYVER_MAJOR=${PYVER_MINOR:0:3}

  function export_paths {
      # Export useful paths based on a common prefix

      # Input: a path prefix

      local prefix=$1
      local pp
      local lp
      local pypath=python${PYVER_MAJOR}/site-packages

      # Compute paths with 64-bit specifics
      if [[ $MACHINE == "x86_64" ]]; then
	  lp=$prefix/lib64:$prefix/lib
	  pp=$prefix/lib64/$pypath:$prefix/lib/$pypath
      else	
	  lp=$prefix/lib
	  pp=$prefix/lib/$pypath
      fi

      # Set paths based on given prefix
      export PATH=$prefix/bin:$PATH
      export CPATH=$prefix/include:$CPATH
      export LD_LIBRARY_PATH=$lp:$LD_LIBRARY_PATH
      export LIBRARY_PATH=$lp:$LIBRARY_PATH
      export PYTHONPATH=$pp:$PYTHONPATH
  }

  # Actually call the export function to set the paths.  If you want more than
  # one such prefix, note that the call *prepends* the new prefix to the
  # existing paths, so later calls take priority.

  export_paths $HOME/usr/local
