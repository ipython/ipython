#!/bin/sh

# Simple backup script for ipython, to keep around a static copy of the whole
# project at the current version point.  We do this by exporting from SVN.

# Config here
IPYTHONSVN=$HOME/ipython/svn/ipython/trunk
BACKUPDIR=$HOME/ipython/backup

####
# Code begins
IPVERSION=`ipython -Version`
IPX=ipython-$IPVERSION
ARCHIVE=$BACKUPDIR/$IPX.tgz

svn export $IPYTHONSVN $IPX

tar czf $ARCHIVE $IPX

rm -rf $IPX

echo "Backup left in: $ARCHIVE"
