.. _core_developer_guide:

=================================
Guide for IPython core Developers
=================================

This guide documents the development of IPython itself.  Alternatively,
developers of third party tools and libraries that use IPython should see the
:doc:`../development/index`.


For instructions on how to make a developer install see :ref:`devinstall`.

Backporting Pull requests
=========================

All pull requests should usually be made against ``master``, if a Pull Request
need to be backported to an earlier release; then it should be tagged with the
correct ``milestone``.

If you tag a pull request with a milestone **before** merging the pull request,
and the base ref is ``master``, then our backport bot should automatically create
a corresponding pull-request that backport on the correct branch.

If you have write access to the IPython repository you can also just mention the
**backport bot** to do the work for you. The bot is evolving so instructions may
be different. At the time of this writing you can use::

    @meeseeksdev[bot] backport [to] <branchname>

The bot will attempt to backport the current pull-request and issue a PR if
possible. 

.. note::

    The ``@`` and ``[bot]`` when mentioning the bot should be optional and can
    be omitted.

If the pull request cannot be automatically backported, the bot should tell you
so on the PR and apply a "Need manual backport" tag to the origin PR.

.. _release_process:

IPython release process
=======================

This document contains the process that is used to create an IPython release.

Conveniently, the ``release`` script in the ``tools`` directory of the ``IPython``
repository automates most of the release process. This document serves as a
handy reminder and checklist for the release manager.

During the release process, you might need the extra following dependencies:

 - ``keyring`` to access your GitHub authentication tokens
 - ``graphviz`` to generate some graphs in the documentation
 - ``ghpro`` to generate the stats

Make sure you have all the required dependencies to run the tests as well.

You can try to ``source tools/release_helper.sh`` when releasing via bash, it 
should guide you through most of the process.


1. Set Environment variables
----------------------------

Set environment variables to document previous release tag, current
release milestone, current release version, and git tag.

These variables may be used later to copy/paste as answers to the script
questions instead of typing the appropriate command when the time comes. These
variables are not used by the scripts directly; therefore, there is no need to
``export`` them. The format for bash is as follows, but note that these values
are just an example valid only for the 5.0 release; you'll need to update them
for the release you are actually making::

    PREV_RELEASE=4.2.1
    MILESTONE=5.0
    VERSION=5.0.0
    BRANCH=master

For `reproducibility of builds <https://reproducible-builds.org/specs/source-date-epoch/>`_,
we recommend setting ``SOURCE_DATE_EPOCH`` prior to running the build; record the used value
of ``SOURCE_DATE_EPOCH`` as it may not be available from build artifact. You
should be able to use ``date +%s`` to get a formatted timestamp::

    SOURCE_DATE_EPOCH=$(date +%s)


2. Create GitHub stats and finish release note
----------------------------------------------

.. note::

    This step is optional if making a Beta or RC release.

.. note::

    Before generating the GitHub stats, verify that all closed issues and pull
    requests have `appropriate milestones
    <https://github.com/ipython/ipython/wiki/Dev:-GitHub-workflow#milestones>`_.
    `This search
    <https://github.com/ipython/ipython/issues?q=is%3Aclosed+no%3Amilestone+is%3Aissue>`_
    should return no results before creating the GitHub stats.

If a major release:

    - merge any pull request notes into what's new::

          python tools/update_whatsnew.py

    - update ``docs/source/whatsnew/development.rst``, to ensure it covers
      the major release features

    - move the contents of ``development.rst`` to ``versionX.rst`` where ``X`` is
      the numerical release version

    - generate summary of GitHub contributions, which can be done with::

          python tools/github_stats.py --milestone $MILESTONE > stats.rst

      which may need some manual cleanup of ``stats.rst``. Add the cleaned
      ``stats.rst`` results to ``docs/source/whatsnew/github-stats-X.rst``
      where ``X`` is the numerical release version (don't forget to add it to
      the git repository as well). If creating a major release, make a new
      ``github-stats-X.rst`` file; if creating a minor release, the content
      from ``stats.rst`` may simply be added to the top of an existing
      ``github-stats-X.rst`` file.

    - Edit ``docs/source/whatsnew/index.rst`` to list the new ``github-stats-X``
      file you just created.

    - You do not need to temporarily remove the first entry called
      ``development``, nor re-add it after the release, it will automatically be
      hidden when releasing a stable version of IPython (if ``_version_extra``
      in ``release.py`` is an empty string.

      Make sure that the stats file has a header or it won't be rendered in
      the final documentation.

To find duplicates and update `.mailmap`, use::

    git log --format="%aN <%aE>" $PREV_RELEASE... | sort -u -f

If a minor release you might need to do some of the above points manually, and
forward port the changes.

3. Make sure the repository is clean
------------------------------------

of any file that could be problematic.
   Remove all non-tracked files with:

   .. code::

       git clean -xfdi

   This will ask for confirmation before removing all untracked files. Make
   sure the ``dist/`` folder is clean to avoid any stale builds from
   previous build attempts.


4. Update the release version number
------------------------------------

Edit ``IPython/core/release.py`` to have the current version.

in particular, update version number and ``_version_extra`` content in
``IPython/core/release.py``.

Step 5 will validate your changes automatically, but you might still want to
make sure the version number matches pep440.

In particular, ``rc`` and ``beta`` are not separated by ``.`` or the ``sdist``
and ``bdist`` will appear as different releases. For example, a valid version
number for a release candidate (rc) release is: ``1.3rc1``. Notice that there
is no separator between the '3' and the 'r'. Check the environment variable
``$VERSION`` as well.

You will likely just have to modify/comment/uncomment one of the lines setting
``_version_extra``


5. Run the `tools/build_release` script
---------------------------------------

Running ``tools/build_release`` does all the file checking and building that
the real release script will do. This makes test installations, checks that
the build procedure runs OK, and tests other steps in the release process.

The ``build_release`` script will in particular verify that the version number
match PEP 440, in order to avoid surprise at the time of build upload.

We encourage creating a test build of the docs as well. 

6. Create and push the new tag
------------------------------

Commit the changes to release.py::

    git commit -am "release $VERSION" -S
    git push origin $BRANCH

(omit the ``-S`` if you are no signing the package)

Create and push the tag::

    git tag -am "release $VERSION" "$VERSION" -s
    git push origin $VERSION

(omit the ``-s`` if you are no signing the package)

Update release.py back to ``x.y-dev`` or ``x.y-maint`` commit and push::

    git commit -am "back to development" -S
    git push origin $BRANCH

(omit the ``-S`` if you are no signing the package)

Now checkout the tag we just made::

    git checkout $VERSION

7. Run the release script
-------------------------

Run the ``release`` script, this step requires having a current wheel, Python
>=3.4 and Python 2.7.::

    ./tools/release

This makes the tarballs and wheels, and puts them under the ``dist/``
folder. Be sure to test the ``wheels``  and the ``sdist`` locally before
uploading them to PyPI. We do not use an universal wheel as each wheel
installs an ``ipython2`` or ``ipython3`` script, depending on the version of
Python it is built for. Using an universal wheel would prevent this.

Check the shasum of files with::

    shasum -a 256 dist/*

and takes notes of them you might need them to update the conda-forge recipes.
Rerun the command and check the hash have not changed::

    ./tools/release
    shasum -a 256 dist/*

Use the following to actually upload the result of the build::

    ./tools/release upload

It should posts them to ``archive.ipython.org`` and to PyPI.

PyPI/Warehouse will automatically hide previous releases. If you are uploading
a non-stable version, make sure to log-in to PyPI and un-hide previous version.


8. Draft a short release announcement
-------------------------------------

The announcement should include:

- release highlights
- a link to the html version of the *What's new* section of the documentation
- a link to upgrade or installation tips (if necessary)

Post the announcement to the mailing list and or blog, and link from Twitter.

.. note::

    If you are doing a RC or Beta, you can likely skip the next steps.

9. Update milestones on GitHub
-------------------------------

These steps will bring milestones up to date:

- close the just released milestone
- open a new milestone for the next release (x, y+1), if the milestone doesn't
  exist already

10. Update the IPython website
------------------------------

The IPython website should document the new release:

- add release announcement (news, announcements)
- update current version and download links
- update links on the documentation page (especially if a major release)

11. Update readthedocs
----------------------

Make sure to update readthedocs and set the latest tag as stable, as well as
checking that previous release is still building under its own tag.

12. Update the Conda-Forge feedstock
------------------------------------

Follow the instructions on `the repository <https://github.com/conda-forge/ipython-feedstock>`_

13. Celebrate!
--------------

Celebrate the release and please thank the contributors for their work. Great
job!



Old Documentation
=================

Out of date documentation is still available and have been kept for archival purposes.

.. note::

  Developers documentation used to be on the IPython wiki, but are now out of
  date. The wiki is though still available for historical reasons: `Old IPython
  GitHub Wiki.  <https://github.com/ipython/ipython/wiki/Dev:-Index>`_
