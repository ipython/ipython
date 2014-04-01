#!/usr/bin/env bash

DOTGIT=`git rev-parse --git-dir`
TOPLEVEL=`git rev-parse --show-toplevel`
TO=${DOTGIT}/hooks
FROM=${TOPLEVEL}/git-hooks

ln -s ${FROM}/post-checkout ${TO}/post-checkout
ln -s ${FROM}/post-merge ${TO}/post-merge
