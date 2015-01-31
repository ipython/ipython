Documenting What's New
----------------------

When making a new pull request that either adds a new feature, or makes a
backwards-incompatible change to IPython, please add a new `.rst` file in this
directory documenting this change as a part of your Pull Request.

This will allow multiple Pull Requests to do the same without conflicting with
one another. Periodically, IPython developers with commit rights will run a
script and populate [development.rst](../development.rst)
with the contents of this directory, and clean it up.

Files which describe new features can have any name, such as
`antigravity-feature.rst`, whereas backwards incompatible changes **must have**
have a filename starting with `incompat-`, such as
`incompat-switching-to-perl.rst`.  Our "What's new" files always have two
sections,  and this prefix scheme will make sure that the backwards incompatible
changes get routed to their proper section.

To merge these files into :file:`whatsnew/development.rst`, run the script :file:`tools/update_whatsnew.py`.
