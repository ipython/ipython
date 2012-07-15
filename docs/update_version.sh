#!/bin/sh
ver=`ipython -V`
sed "s/__version__/${ver}/" manual_base.lyx > manual.lyx
