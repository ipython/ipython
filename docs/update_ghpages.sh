#!/usr/bin/env sh
# pick repo for gh-pages branch
repo=origin

if [ ! -d gh-pages ]; then
    echo "setting up gh-pages subdir"
    mkdir gh-pages || exit -1
    cp -r ../.git gh-pages/ || exit -1
    cd gh-pages || exit -1
    init=0
    git checkout $repo/gh-pages || init=1
    if [ "$init" != "0" ]; then
        echo "initializing gh-pages repo"
        git symbolic-ref HEAD refs/heads/gh-pages || exit -1
        rm .git/index || exit -1
        git clean -fdx || exit -1
        touch index.html
        git add .
        git commit -a -m 'init gh-pages' || exit -1
        git push origin HEAD:gh-pages
    fi
    cd ..
fi
echo "updating local gh-pages with html build"
rsync -va build/html/ gh-pages/ --delete --exclude .git || exit -1
cd gh-pages
git add .
git commit -a || exit -1
echo "pushing to remote gh-pages"
# pwd
git push $repo HEAD:gh-pages
