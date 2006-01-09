#!/usr/bin/env python
"""Simple wrapper to build IPython as an egg (setuptools format)."""

import sys

import pkg_resources
pkg_resources.require("setuptools")
import setuptools

sys.argv=['','bdist_egg']
execfile('setup.py')
