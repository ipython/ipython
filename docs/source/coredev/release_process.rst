.. _release_process:

=======================
IPython release process
=======================

This document contains the process that is used to create an IPython release.

Conveniently, the `release` script in the `tools` directory of the `IPython`
repository automates most of the release process. This document serves as a
handy reminder and checklist for the release manager.

1. Set Environment variables
----------------------------

Set environment variables to document previous release tag, current
release milestone, current release version, and git tag::

    PREV_RELEASE=rel-1.0.0
    MILESTONE=1.1
    VERSION=1.1.0
    TAG="rel-$VERSION"
    BRANCH=master

These variables may be used later to copy/paste as answers to the script
questions instead of typing the appropriate command when the time comes. These
variables are not used by the scripts directly; therefore, there is no need to
`export` the variables.

2. Create GitHub stats and finish release note
----------------------------------------------

.. note::

    Before generating the GitHub stats, verify that all closed issues and
    pull requests have `appropriate milestones <https://github.com/ipython/ipython/wiki/Dev%3A-GitHub-workflow#milestones>`_.
    `This search <https://github.com/ipython/ipython/issues?q=is%3Aclosed+no%3Amilestone+is%3Aissue>`_
    should return no results before creating the GitHub stats.

If a major release:

    - merge any pull request notes into what's new::

          python tools/update_whatsnew.py

    - update `docs/source/whatsnew/development.rst`, to ensure it covers
      the major release features
    - move the contents of `development.rst` to `versionX.rst` where `X` is
      the numerical release version
    - generate summary of GitHub contributions, which can be done with::

          python tools/github_stats.py --milestone $MILESTONE > stats.rst

      which may need some manual cleanup of `stats.rst`. Add the cleaned
      `stats.rst` results to `docs/source/whatsnew/github-stats-X.rst` where
      `X` is the numerical release version. If creating a major release, make
      a new `github-stats-X.rst` file; if creating a minor release, the
      content from `stats.rst` may simply be added to the top of an existing
      `github-stats-X.rst` file.

To find duplicates and update `.mailmap`, use::

    git log --format="%aN <%aE>" $PREV_RELEASE... | sort -u -f


3. Run the `tools/build_release` script
---------------------------------------

Running `tools/build_release` does all the file checking and building that
the real release script will do. This makes test installations, checks that
the build procedure runs OK, and tests other steps in the release process.

We encourage creating a test build of the docs as well.

4. Create and push the new tag
------------------------------

Edit `IPython/core/release.py` to have the current version.

Commit the changes to release.py and jsversion::

    git commit -am "release $VERSION"
    git push origin $BRANCH

Create and push the tag::

    git tag -am "release $VERSION" "$TAG"
    git push origin --tags

Update release.py back to `x.y-dev` or `x.y-maint`, and push::

    git commit -am "back to development"
    git push origin $BRANCH

5. Get a fresh clone
--------------------

Get a fresh clone of the tag for building the release::

    cd /tmp
    git clone --depth 1 https://github.com/ipython/ipython.git -b "$TAG"

6. Run the release script
-------------------------

Run the `release` script::

    cd tools && ./release

This makes the tarballs, zipfiles, and wheels.  It posts
them to archive.ipython.org and registers the release with PyPI.

This step requires having a current wheel, Python 3.4 and Python 2.7.

7. Draft a short release announcement
-------------------------------------

The announcement should include:

- release highlights
- a link to the html version of the *What's new* section of the documentation
- a link to upgrade or installation tips (if necessary)

Post the announcement to the mailing list, and link from Twitter.

8. Update milestones on GitHub
------------------------------

These steps will bring milestones up to date:

- close the just released milestone
- open a new milestone for the next release (x, y+1), if the milestone doesn't
  exist already

9. Update the IPython website
-----------------------------

The IPython website should document the new release:

- add release announcement (news, announcements)
- update current version and download links
- update links on the documentation page (especially if a major release)

10. Celebrate!
--------------

Celebrate the release and please thank the contributors for their work. Great
job!

