# Other config options for blame are markUnblamables and markIgnoredLines.
# See docs for more details:
# https://git-scm.com/docs/git-config#Documentation/git-config.txt-blameignoreRevsFile

# Uncomment below and rerun script to enable an option.
# git config blame.markIgnoredLines
# git config blame.markUnblamables

git config blame.ignoreRevsFile .git-blame-ignore-revs
git config --get blame.ignoreRevsFile
