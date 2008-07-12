# encoding: utf-8
"""
setup.py

Setuptools installer script for generating a Cocoa plugin for the 
IPython cocoa frontend

Author: Barry Wark
"""
__docformat__ = "restructuredtext en"

#-----------------------------------------------------------------------------
#  Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

from setuptools import setup

infoPlist = dict(
	CFBundleDevelopmentRegion='English',
	CFBundleIdentifier='org.scipy.ipython.cocoa_frontend',
	NSPrincipalClass='IPythonCocoaController',
)

setup(
	plugin=['IPythonCocoaFrontendLoader.py'],
    setup_requires=['py2app'],
	options=dict(py2app=dict(
		plist=infoPlist,
		site_packages=True,
		excludes=['IPython','twisted','PyObjCTools']
	)),
)