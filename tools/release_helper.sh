# Simple tool to help for release
# when releasing with bash or zsh, simply source it to get asked questions:
#
#     source tools/release_helper.sh
#
# VERSION, NEXT_VERSION, BRANCH and REMOTE can be set beforehand; they are
# used as defaults for the prompts.
#
# Every command is shown before it runs, both as written and with the
# variables expanded, and you can skip it.
#
# Publishing to PyPI is done by the publish workflow when the tag is pushed;
# it requires the tag to be exactly the version built from release.py.

# misc check before starting
RED=$(tput setaf 1)
GREEN=$(tput setaf 2)
YELLOW=$(tput setaf 3)
BLUE=$(tput setaf 4)
MAGENTA=$(tput setaf 5)
CYAN=$(tput setaf 6)
NOR=$(tput sgr0)

RELEASE_PY=IPython/core/release.py
VERSION_RE='^[0-9]+\.[0-9]+\.[0-9]+$'

# Read a single key into $value (empty when Enter is pressed).
read_key(){
    if [ "$ZSH_NAME" = "zsh" ] ; then
        read -k1 value
        value=${value%$'\n'}
    else
        read -n1 value
    fi
    if [ -n "$value" ]; then
        echo
    fi
}

ask_section(){
    echo
    echo $BLUE"$1"$NOR
    echo -n $GREEN"Press Enter to continue, S to skip: "$NOR
    read_key
    if [ -z "$value" ] || [ "$value" = 'y' ]; then
        return 0
    fi
    return 1
}

# Like ask_section, but skipped unless explicitly asked for with 'y'.
ask_section_default_skip(){
    echo
    echo $BLUE"$1"$NOR
    echo -n $GREEN"Press y to run it, Enter (or any other key) to skip: "$NOR
    read_key
    if [ "$value" = 'y' ]; then
        return 0
    fi
    return 1
}

pause(){
    echo $GREEN"${1:-Press enter to continue}"$NOR
    read
}

# Substitute the variables this script uses into a command template.
expand_cmd(){
    local s="$1"
    s=${s//\$NEXT_VERSION/$NEXT_VERSION}
    s=${s//\$VERSION/$VERSION}
    s=${s//\$BRANCH/$BRANCH}
    s=${s//\$REMOTE/$REMOTE}
    s=${s//\$RELEASE_PY/$RELEASE_PY}
    s=${s//\$SOURCE_DATE_EPOCH/$SOURCE_DATE_EPOCH}
    printf '%s\n' "$s"
}

# Show a command (as written, and expanded), then run it on Enter.
# Pass it in single quotes so it is expanded only when run.
# Returns 1 if skipped, otherwise the command's exit status.
run_cmd(){
    local expanded
    expanded=$(expand_cmd "$1")
    echo
    echo $BLUE"\$ $1"$NOR
    if [ "$expanded" != "$1" ]; then
        echo $CYAN"\$ $expanded"$NOR
    fi
    echo -n $GREEN"Press Enter to run, S to skip: "$NOR
    read_key
    if [ -n "$value" ] && [ "$value" != 'y' ]; then
        echo $YELLOW"skipped"$NOR
        return 1
    fi
    eval "$1"
}

is_version(){
    [[ "$1" =~ $VERSION_RE ]]
}

# Version string release.py currently computes, without importing IPython.
release_py_version(){
    python -c 'import sys; ns = {}; exec(open(sys.argv[1]).read(), ns); print(ns["__version__"])' "$RELEASE_PY"
}

# set_release_py X.Y.Z release|dev
# Set major/minor/patch in release.py and toggle the full-release line.
set_release_py(){
    local major minor patch extra_expr
    IFS=. read -r major minor patch <<< "$1"
    if [ "$2" = release ]; then
        # uncomment `_version_extra = ""  # Uncomment this for full releases`
        extra_expr='/Uncomment/s/^# //'
    else
        # comment it again (only once)
        extra_expr='/Uncomment/s/^(# )?/# /'
    fi
    sed -i.bkp -E \
        -e "s/^_version_major = .*/_version_major = $major/" \
        -e "s/^_version_minor = .*/_version_minor = $minor/" \
        -e "s/^_version_patch = .*/_version_patch = $patch/" \
        -e "$extra_expr" \
        "$RELEASE_PY" && rm -f "$RELEASE_PY.bkp"
}

# check_release_py EXPECTED
check_release_py(){
    local got
    got=$(release_py_version)
    if [ "$got" != "$1" ]; then
        echo $RED"$RELEASE_PY gives version '$got', expected '$1'."$NOR
        return 1
    fi
    echo $GREEN"$RELEASE_PY gives version '$got'."$NOR
}

maybe_edit(){
    echo
    echo $BLUE"$1"$NOR
    echo -n $GREEN"Press ${BLUE}e$GREEN to Edit ${BLUE}$1$GREEN, any other keys to skip: "$NOR
    read_key
    if [ "$value" = 'e' ]; then
        eval "$EDITOR \"\$1\""
    fi
}

check_module(){
    # check_module module [why]
    if ! python -c "import $1" 2>/dev/null; then
        echo $YELLOW"  missing python module '$1'${2:+ ($2)}"$NOR
    fi
}

release_main(){
    echo "Checking tools..."
    check_module build "needed to build"
    check_module pytest "needed to run tests"
    check_module sphinx "only for building the docs locally"
    check_module sphinx_rtd_theme "only for building the docs locally"
    check_module numpy "only for building the docs locally"
    check_module matplotlib "only for building the docs locally"
    check_module twine "only for manual upload"

    echo "Will use $BLUE'$EDITOR'$NOR to edit files when necessary"

    # The tag must be exactly X.Y.Z: the publish workflow compares the tag
    # name with the built version string and refuses to publish on any
    # mismatch (e.g. a "9.19" tag for a 9.19.0 release).
    while true; do
        echo -n "VERSION to release (X.y.z) [$VERSION]: "
        read input
        VERSION=${input:-$VERSION}
        is_version "$VERSION" && break
        echo $RED"VERSION must be of the form X.Y.Z (e.g. 9.19.0), got '$VERSION'"$NOR
    done

    echo -n "BRANCH (main|X.y) [${BRANCH:-main}]: "
    read input
    BRANCH=${input:-${BRANCH:-main}}

    local major minor patch default_next
    IFS=. read -r major minor patch <<< "$VERSION"
    if [ "$BRANCH" = main ]; then
        default_next="$major.$((minor + 1)).0"
    else
        default_next="$major.$minor.$((patch + 1))"
    fi
    NEXT_VERSION=${NEXT_VERSION:-$default_next}
    # don't reuse a stale NEXT_VERSION from a previous release
    if ! is_version "$NEXT_VERSION" || [ "$NEXT_VERSION" = "$VERSION" ]; then
        NEXT_VERSION=$default_next
    fi
    while true; do
        echo -n "NEXT_VERSION, the next dev version (X.y.z) [$NEXT_VERSION]: "
        read input
        NEXT_VERSION=${input:-$NEXT_VERSION}
        is_version "$NEXT_VERSION" && [ "$NEXT_VERSION" != "$VERSION" ] && break
        echo $RED"NEXT_VERSION must be of the form X.Y.Z and differ from $VERSION, got '$NEXT_VERSION'"$NOR
    done

    echo -n "REMOTE to push to [${REMOTE:-origin}]: "
    read input
    REMOTE=${input:-${REMOTE:-origin}}
    echo "Remote $BLUE$REMOTE$NOR is $BLUE$(git remote get-url "$REMOTE")$NOR"

    local current
    current=$(git rev-parse --abbrev-ref HEAD)
    if [ "$current" != "$BRANCH" ]; then
        echo $RED"You are on '$current', not on '$BRANCH'."$NOR
        return 1
    fi
    if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
        echo $RED"Tag $VERSION already exists locally."$NOR
        return 1
    fi
    if git ls-remote --exit-code --tags "$REMOTE" "refs/tags/$VERSION" >/dev/null 2>&1; then
        echo $RED"Tag $VERSION already exists on $REMOTE."$NOR
        return 1
    fi

    echo
    echo "Releasing $MAGENTA$VERSION$NOR from $MAGENTA$BRANCH$NOR, then back to $MAGENTA$NEXT_VERSION.dev$NOR"

    if ask_section "Updating what's new with information from docs/source/whatsnew/pr"
    then
        run_cmd 'python tools/update_whatsnew.py'
        echo
        echo $BLUE"please move the contents of docs/source/whatsnew/development.rst to version-X.rst"$NOR
        pause
    fi

    echo
    echo "Cleaning repository"
    run_cmd 'git clean -xfdi'

    echo
    echo "Setting version $VERSION in $RELEASE_PY"
    run_cmd 'set_release_py "$VERSION" release'
    git diff | cat
    maybe_edit "$RELEASE_PY"
    if ! check_release_py "$VERSION"; then
        echo $RED"The publish workflow would refuse a '$VERSION' tag. Fix $RELEASE_PY and source this script again."$NOR
        return 1
    fi

    if ask_section_default_skip "Build the documentation ? (Read the Docs builds them)"
    then
        run_cmd 'make html -C docs'
        pause "Check the docs, press enter to continue"
    fi

    if ask_section "Should we commit, tag, push... etc ? "
    then
        # release.py may have been edited since the check above.
        check_release_py "$VERSION" || return 1

        run_cmd 'git commit -am "release $VERSION" -S'
        echo $GREEN"Make sure you can push"$NOR
        run_cmd 'git push $REMOTE $BRANCH'
        run_cmd 'git tag -am "release $VERSION" "$VERSION" -s'
        echo $GREEN"Pushing the tag triggers the publish workflow, which uploads to PyPI."$NOR
        run_cmd 'git push $REMOTE $VERSION'

        echo
        echo "Back to dev: setting version $NEXT_VERSION.dev in $RELEASE_PY"
        run_cmd 'set_release_py "$NEXT_VERSION" dev'
        git diff | cat
        maybe_edit "$RELEASE_PY"
        check_release_py "$NEXT_VERSION.dev"

        run_cmd 'git commit -am "back to dev"'
        run_cmd 'git push $REMOTE $BRANCH'
        run_cmd 'git checkout tags/$VERSION'
    fi

    if ask_section_default_skip "Should we build and upload to PyPI manually ? (the publish workflow does this when the tag is pushed)"
    then
        run_cmd 'export SOURCE_DATE_EPOCH=$(git show -s --format=%ct HEAD)'
        echo $BLUE"SOURCE_DATE_EPOCH set to $SOURCE_DATE_EPOCH"$NOR

        run_cmd 'tools/build_release'
        run_cmd 'shasum -a 256 dist/*'

        echo $BLUE"We are going to rebuild, note the hash above, and compare them to the rebuild"$NOR
        run_cmd 'tools/build_release'
        echo $RED"Check the shasum for SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH"$NOR
        run_cmd 'shasum -a 256 dist/*'

        if ask_section_default_skip "upload packages ?"
        then
            run_cmd 'twine upload --verbose dist/*.tar.gz dist/*.whl'
        fi
    fi
}

release_main
