# Simple tool to help for release
# when releasing with bash, simplei source it to get asked questions. 

# misc check before starting

python -c 'import keyring'
python -c 'import twine'
python -c 'import sphinx'
python -c 'import sphinx_rtd_theme'
python -c 'import nose'

echo -n 'PREV_RELEASE (X.y.z):'
read PREV_RELEASE
echo -n 'MILESTONE (X.y):'
read MILESTONE
echo -n 'VERSION (X.y.z):'
read VERSION
echo -n 'branch (master|X.y):'
read branch

BLACK=$(tput setaf 1)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)
NOR=$(tput sgr0)

echo 
echo $BLUE"Updating what's new with informations from docs/source/whatsnew/pr"$NOR
python tools/update_whatsnew.py

echo
echo $BLUE"please move the contents of "docs/source/whatsnew/development.rst" to version-X.rst"$NOR
echo $GREEN"Press enter to continue"$NOR
read

echo 
echo $BLUE"here are all the authors that contributed to this release:"$NOR
git log --format="%aN <%aE>" $PREV_RELEASE... | sort -u -f

echo 
echo $BLUE"If you see any duplicates cancel (Ctrl-C), then edit .mailmap."$GREEN"Press enter to continue:"$NOR
read

echo $BLUE"generating stats"$NOR
python tools/github_stats.py --milestone $MILESTONE > stats.rst

echo $BLUE"stats.rst files generated."$NOR
echo $GREEN"Please merge it with the right file (github-stats-X.rst) and commit."$NOR
echo $GREEN"press enter to continue."$NOR
read

echo "Cleaning repository"
git clean -xfdi

echo $GREEN"please update version number in ${RED}IPython/core/release.py${NOR} , Do not commit yet – we'll do it later."$NOR

echo $GREEN"Press enter to continue"$NOR
read

echo 
echo "Attempting to build the docs.."
make html -C docs

echo 
echo $GREEN"Check the docs, press enter to continue"$NOR
read

echo
echo $BLUE"Attempting to build package..."$NOR

tools/build_release

echo
echo "Let\'s commit : git commit -am \"release $VERSION\" -S"
echo $GREEN"Press enter to continue"$NOR
read
git commit -am "release $VERSION" -S

echo
echo "git push origin \$BRANCH ?"
echo "Press enter to continue"
read
git push origin $BRANCH
# git tag -am "release $VERSION" "$VERSION" -s
# git push origin $VERSION

