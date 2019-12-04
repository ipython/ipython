# Simple tool to help for release
# when releasing with bash, simple source it to get asked questions. 

# misc check before starting

python -c 'import keyring'
python -c 'import twine'
python -c 'import sphinx'
python -c 'import sphinx_rtd_theme'
python -c 'import nose'


BLACK=$(tput setaf 1)
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
WHITE=$(tput setaf 7)
NOR=$(tput sgr0)


echo -n "PREV_RELEASE (X.y.z) [$PREV_RELEASE]: "
read input
PREV_RELEASE=${input:-$PREV_RELEASE}
echo -n "MILESTONE (X.y) [$MILESTONE]: "
read input
MILESTONE=${input:-$MILESTONE}
echo -n "VERSION (X.y.z) [$VERSION]:"
read input
VERSION=${input:-$VERSION}
echo -n "BRANCH (master|X.y) [$BRANCH]:"
read input
BRANCH=${input:-$BRANCH}

ask_section(){
    echo
    echo $BLUE"$1"$NOR 
    echo -n $GREEN"Press Enter to continue, S to skip: "$GREEN
    read -n1 value
    echo 
    if [ -z $value ] || [ $value = 'y' ]  ; then
        return 0
    fi
    return 1
}



echo 
if ask_section "Updating what's new with informations from docs/source/whatsnew/pr"
then
    python tools/update_whatsnew.py

    echo
    echo $BLUE"please move the contents of "docs/source/whatsnew/development.rst" to version-X.rst"$NOR
    echo $GREEN"Press enter to continue"$NOR
    read
fi

if ask_section "Gen Stats, and authors"
then

    echo 
    echo $BLUE"here are all the authors that contributed to this release:"$NOR
    git log --format="%aN <%aE>" $PREV_RELEASE... | sort -u -f

    echo 
    echo $BLUE"If you see any duplicates cancel (Ctrl-C), then edit .mailmap."
    echo $GREEN"Press enter to continue:"$NOR
    read

    echo $BLUE"generating stats"$NOR
    python tools/github_stats.py --milestone $MILESTONE > stats.rst

    echo $BLUE"stats.rst files generated."$NOR
    echo $GREEN"Please merge it with the right file (github-stats-X.rst) and commit."$NOR
    echo $GREEN"press enter to continue."$NOR
    read

fi

echo "Cleaning repository"
git clean -xfdi

echo $GREEN"please update version number in ${RED}IPython/core/release.py${NOR} , Do not commit yet – we'll do it later."$NOR

echo $GREEN"Press enter to continue"$NOR
read

if ask_section "Build the documentation ?"
then
    make html -C docs
    echo 
    echo $GREEN"Check the docs, press enter to continue"$NOR
    read

fi

echo
echo $BLUE"Attempting to build package..."$NOR

tools/build_release
rm dist/*

if ask_section "Should we commit, tag, push... etc ? "
then
   echo
   echo "Let's commit : git commit -am \"release $VERSION\" -S"
   echo $GREEN"Press enter to commit"$NOR
   read
   git commit -am "release $VERSION" -S
   
   echo
   echo $BLUE"git push origin \$BRANCH ($BRANCH)?"$NOR
   echo $GREEN"Make sure you can push"$NOR
   echo $GREEN"Press enter to continue"$NOR
   read
   git push origin $BRANCH
   
   echo
   echo "Let's tag : git tag -am \"release $VERSION\" \"$VERSION\" -s"
   echo $GREEN"Press enter to tag commit"$NOR
   read
   git tag -am "release $VERSION" "$VERSION" -s
   
   echo
   echo $BLUE"And push the tag: git push origin \$VERSION ?"$NOR
   echo $GREEN"Press enter to continue"$NOR
   read
   git push origin $VERSION
   
   
   echo $GREEN"please update version number and back to .dev in ${RED}IPython/core/release.py"
   echo ${BLUE}"Do not commit yet – we'll do it later."$NOR
   
   echo $GREEN"Press enter to continue"$NOR
   read
   
   echo
   echo "Let's commit : git commit -am \"back to dev\" -S"
   echo $GREEN"Press enter to commit"$NOR
   read
   git commit -am "back to dev" -S
   
   echo
   echo $BLUE"let's : git checkout $VERSION"$NOR
   echo $GREEN"Press enter to continue"$NOR
   read
   git checkout $VERSION
fi

if ask_section "Should we build and release ?"
then

    echo
    echo $BLUE"Attempting to build package..."$NOR

    tools/build_release

    echo '$ shasum -a 256 dist/*'
    shasum -a 256 dist/*

    if ask_section "upload packages ?"
    then 
       tools/build_release upload
    fi
fi
