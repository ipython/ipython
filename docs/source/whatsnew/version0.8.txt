========================================
0.8 series
========================================

Release 0.8.4
=============

This was a quick release to fix an unfortunate bug that slipped into the 0.8.3
release.  The ``--twisted`` option was disabled, as it turned out to be broken
across several platforms.


Release 0.8.3
=============
  
* pydb is now disabled by default (due to %run -d problems). You can enable
  it by passing -pydb command line argument to IPython. Note that setting
  it in config file won't work.

  
Release 0.8.2
=============

* %pushd/%popd behave differently; now "pushd /foo" pushes CURRENT directory 
  and jumps to /foo. The current behaviour is closer to the documented 
  behaviour, and should not trip anyone.

  
Older releases
==============

Changes in earlier releases of IPython are described in the older file
``ChangeLog``.  Please refer to this document for details.

