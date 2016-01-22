.. _developer_guide:

=========================
IPython developer's guide
=========================

This are two categories of developer focused documentation:

1. Documentation for developers of *IPython itself*.
2. Documentation for developers of third party tools and libraries
   that use IPython.

This part of our documentation only contains information in the second category.

Developers interested in working on IPython itself should consult
our `developer information <https://github.com/ipython/ipython/wiki/Dev:-Index>`_ 
on the IPython GitHub wiki.

.. toctree::
   :maxdepth: 1

   how_ipython_works
   wrapperkernels
   execution
   lexer
   pycompat
   config
   inputhook_app

Making an IPython release
=========================

Make sure the repository is clean of any file that could be problematic. 
You can remove all non-tracked files with:

.. code::

    $ git clean -xfdi

This would ask you for confirmation before removing all untracked files. Make
sure the ``dist/`` folder is clean and avoid stale build from
previous attempts.

1. Update version number in ``IPython/core/release.py``.

Make sure the version number match pep440, in particular, `rc` and `beta` are
not separated by `.` or the `sdist` and `bdist` will appear as different
releases.

2. Commit and tag the release with the current version number:

.. code::

    git commit -am "release $VERSION"
    git tag $VERSION


3. You are now ready to build the ``sdist`` and ``wheel``:

.. code::

    $ python setup.py sdist --formats=zip,gztar
    $ python setup.py bdist_wheel


4. You can now test the ``wheel`` and the ``sdist`` locally before uploading to PyPI.
Make sure to use `twine <https://github.com/pypa/twine>`_ to upload the archives over SSL.

.. code::

    $ twine upload dist/*

5. If all went well, change the ``IPython/core/release.py`` back adding the ``.dev`` suffix.

6. Push directly on master, not forgetting to push ``--tags``.

