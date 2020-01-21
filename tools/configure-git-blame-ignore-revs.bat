rem Other config options for blame are markUnblamables and markIgnoredLines.
rem See docs for more details:
rem https://git-scm.com/docs/git-config#Documentation/git-config.txt-blameignoreRevsFile

rem Uncomment below and rerun script to enable an option.
rem git config blame.markIgnoredLines
rem git config blame.markUnblamables

git config blame.ignoreRevsFile .git-blame-ignore-revs
git config --get blame.ignoreRevsFile
