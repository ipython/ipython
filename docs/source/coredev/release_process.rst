This document contains notes about the process that is used to release IPython.
Our release process is currently not very formal and could be improved.

Most of the release process is automated by the `release` script in the `tools`
directory of our main repository.  This document is just a handy reminder for
the release manager.

# 0. Environment variables

You can set some env variables to note previous release tag and current release milestone, version, and git tag:

    PREV_RELEASE=rel-1.0.0
    MILESTONE=1.1
    VERSION=1.1.0
    TAG="rel-$VERSION"
    BRANCH=master

These will be used later if you want to copy/paste, or you can just type the appropriate command when the time comes. These variables are not used by scripts (hence no `export`).

# 1. Finish release notes

- If a major release:

  - merge any pull request notes into what's new:

          python tools/update_whatsnew.py

  - update `docs/source/whatsnew/development.rst`, to ensure it covers the major points.
  - move the contents of `development.rst` to `versionX.rst`
- generate summary of GitHub contributions, which can be done with:

        python tools/github_stats.py --milestone $MILESTONE > stats.rst

  which may need some manual cleanup. Add the cleaned up result and add it to `docs/source/whatsnew/github-stats-X.rst` (make a new file, or add it to the top, depending on whether it is a major release).
  You can use:

        git log --format="%aN <%aE>" $PREV_RELEASE... | sort -u -f

  to find duplicates and update `.mailmap`.
  Before generating the GitHub stats, verify that all closed issues and pull requests [have appropriate milestones](https://github.com/ipython/ipython/wiki/Dev%3A-GitHub-workflow#milestones). [This search](https://github.com/ipython/ipython/issues?q=is%3Aclosed+no%3Amilestone+is%3Aissue) should return no results.

# 2. Run the `tools/build_release` script

This does all the file checking and building that the real release script will do.
This will let you do test installations, check that the build procedure runs OK, etc.
You may want to also do a test build of the docs.

# 3. Create and push the new tag

Edit `IPython/core/release.py` to have the current version.

Commit the changes to release.py and jsversion:

    git commit -am "release $VERSION"
    git push origin $BRANCH

Create and push the tag:

    git tag -am "release $VERSION" "$TAG"
    git push origin --tags

Update release.py back to `x.y-dev` or `x.y-maint`, and push:

    git commit -am "back to development"
    git push origin $BRANCH

# 4. Get a fresh clone of the tag for building the release:

    cd /tmp
    git clone --depth 1 https://github.com/ipython/ipython.git -b "$TAG" 

# 5. Run the `release` script

    cd tools && ./release

This makes the tarballs, zipfiles, and wheels.  It posts them to archive.ipython.org and
registers the release with PyPI.

This will require that you have current wheel, Python 3.4 and Python 2.7.

# 7. Update the IPython website

- release announcement (news, announcements)
- update current version and download links
- (If major release) update links on the documentation page

# 8. Drafting a short release announcement

This should include i) highlights and ii) a link to the html version of
the *What's new* section of the documentation.

Post to mailing list, and link from Twitter.

# 9. Update milestones on GitHub

- close the milestone you just released
- open new milestone for (x, y+1), if it doesn't exist already

# 10. Celebrate!
