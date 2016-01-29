.. making_release::

Making an IPython release
=========================

1. Make sure the repository is clean of any file that could be problematic.
   Remove all non-tracked files with:

   .. code::

       git clean -xfdi

   This will ask for confirmation before removing all untracked files. Make
   sure the ``dist/`` folder is clean to avoid any stale builds from
   previous build attempts.

2. Update version number and ``_version_extra`` content in
   ``IPython/core/release.py``.

   Make sure the version number matches pep440, in particular, `rc` and `beta`
   are not separated by `.` or the `sdist` and `bdist` will appear as different
   releases. For example, a valid version number for a release candidate (rc)
   release is: ``1.3rc1``. Notice that there is no separator between the '3'
   and the 'r'.


3. Commit and tag the release with the current version number:

   .. code::

       git commit -am "release $VERSION"
       git tag $VERSION


4. Build the ``sdist`` and ``wheel``:

   .. code::

       python setup.py sdist --formats=zip,gztar
       python2 setup.py bdist_wheel
       python3 setup.py bdist_wheel


5. Be sure to test the ``wheel`` and the ``sdist`` locally before uploading
   them to PyPI. Make sure to use `twine <https://github.com/pypa/twine>`_ to
   upload these archives over SSL.

   .. code::

       $ twine upload dist/*

6. If all went well, change the ``_version_extra = ''`` in
   ``IPython/core/release.py`` back to the ``.dev`` suffix, or
   ``_version_extra='.dev'``.

7. Push directly to master, remembering to push ``--tags`` too.