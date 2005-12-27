# -*- coding: utf-8 -*-
"""sys.excepthook for IPython itself, leaves a detailed report on disk.

$Id: CrashHandler.py 958 2005-12-27 23:17:51Z fperez $"""

#*****************************************************************************
#       Copyright (C) 2001-2004 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__   = '%s <%s>' % Release.authors['Fernando']
__license__  = Release.license
__version__  = Release.version

#****************************************************************************
# Required modules

# From the standard library
import os
import sys
from pprint import pprint,pformat

# Homebrewed
from IPython.Itpl import Itpl,itpl,printpl
from IPython.ColorANSI import ColorScheme,ColorSchemeTable  # too long names
from IPython import ultraTB
from IPython.genutils import *

#****************************************************************************
class CrashHandler:
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""

    def __init__(self,IP):
        self.IP = IP  # IPython instance
        self.bug_contact = Release.authors['Fernando'][0]
        self.mailto = Release.authors['Fernando'][1]

    def __call__(self,etype, evalue, etb):

        # Report tracebacks shouldn't use color in general (safer for users)
        color_scheme = 'NoColor'

        # Use this ONLY for developer debugging (keep commented out for release)
        #color_scheme = 'Linux'   # dbg
        
        try:
            rptdir = self.IP.rc.ipythondir
        except:
            rptdir = os.getcwd()
        if not os.path.isdir(rptdir):
            rptdir = os.getcwd()
        self.report_name = os.path.join(rptdir,'IPython_crash_report.txt')
        self.TBhandler = ultraTB.VerboseTB(color_scheme=color_scheme,long_header=1)
        traceback = self.TBhandler.text(etype,evalue,etb,context=31)

        # print traceback to screen
        print >> sys.stderr, traceback

        # and generate a complete report on disk
        try:
            report = open(self.report_name,'w')
        except:
            print >> sys.stderr, 'Could not create crash report on disk.'
            return

        msg = itpl('\n'+'*'*70+'\n'
"""
Oops, IPython crashed. We do our best to make it stable, but...

A crash report was automatically generated with the following information:
  - A verbatim copy of the traceback above this text.
  - A copy of your input history during this session.
  - Data on your current IPython configuration.

It was left in the file named:
\t'$self.report_name'
If you can email this file to the developers, the information in it will help
them in understanding and correcting the problem.

You can mail it to $self.bug_contact at $self.mailto
with the subject 'IPython Crash Report'.

If you want to do it now, the following command will work (under Unix):
mail -s 'IPython Crash Report' $self.mailto < $self.report_name

To ensure accurate tracking of this issue, please file a report about it at:
http://www.scipy.net/roundup/ipython  (IPython's online bug tracker).
""")
        print >> sys.stderr, msg

        sec_sep = '\n\n'+'*'*75+'\n\n'
        report.write('*'*75+'\n\n'+'IPython post-mortem report\n\n')
        report.write('IPython version: %s \n\n' % Release.version)
        report.write('SVN revision   : %s \n\n' % Release.revision)
        report.write('Platform info  : os.name -> %s, sys.platform -> %s' %
                     (os.name,sys.platform) )
        report.write(sec_sep+'Current user configuration structure:\n\n')
        report.write(pformat(self.IP.rc.dict()))
        report.write(sec_sep+'Crash traceback:\n\n' + traceback)
        try:
            report.write(sec_sep+"History of session input:")
            for line in self.IP.user_ns['_ih']:
                report.write(line)
            report.write('\n*** Last line of input (may not be in above history):\n')
            report.write(self.IP._last_input_line+'\n')
        except:
            pass
        report.close()
