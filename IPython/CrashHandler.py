# -*- coding: utf-8 -*-
"""sys.excepthook for IPython itself, leaves a detailed report on disk.

$Id: CrashHandler.py 2908 2007-12-30 21:07:46Z vivainio $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez. <fperez@colorado.edu>
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
    """Customizable crash handlers for IPython-based systems.

    Instances of this class provide a __call__ method which can be used as a
    sys.excepthook, i.e., the __call__ signature is:

        def __call__(self,etype, evalue, etb)

    """

    def __init__(self,IP,app_name,contact_name,contact_email,
                 bug_tracker,crash_report_fname,
                 show_crash_traceback=True):
        """New crash handler.

        Inputs:

        - IP: a running IPython instance, which will be queried at crash time
        for internal information.

        - app_name: a string containing the name of your application.

        - contact_name: a string with the name of the person to contact.

        - contact_email: a string with the email address of the contact.

        - bug_tracker: a string with the URL for your project's bug tracker.

        - crash_report_fname: a string with the filename for the crash report
        to be saved in.  These reports are left in the ipython user directory
        as determined by the running IPython instance.

        Optional inputs:
        
        - show_crash_traceback(True): if false, don't print the crash
        traceback on stderr, only generate the on-disk report


        Non-argument instance attributes:

        These instances contain some non-argument attributes which allow for 
        further customization of the crash handler's behavior.  Please see the
        source for further details.
        """

        # apply args into instance
        self.IP = IP  # IPython instance
        self.app_name = app_name
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.bug_tracker = bug_tracker
        self.crash_report_fname = crash_report_fname
        self.show_crash_traceback = show_crash_traceback
        
        # Hardcoded defaults, which can be overridden either by subclasses or
        # at runtime for the instance.

        # Template for the user message.  Subclasses which completely override
        # this, or user apps, can modify it to suit their tastes.  It gets
        # expanded using itpl, so calls of the kind $self.foo are valid.
        self.user_message_template = """
Oops, $self.app_name crashed. We do our best to make it stable, but...

A crash report was automatically generated with the following information:
  - A verbatim copy of the crash traceback.
  - A copy of your input history during this session.
  - Data on your current $self.app_name configuration.

It was left in the file named:
\t'$self.crash_report_fname'
If you can email this file to the developers, the information in it will help
them in understanding and correcting the problem.

You can mail it to: $self.contact_name at $self.contact_email
with the subject '$self.app_name Crash Report'.

If you want to do it now, the following command will work (under Unix):
mail -s '$self.app_name Crash Report' $self.contact_email < $self.crash_report_fname

To ensure accurate tracking of this issue, please file a report about it at:
$self.bug_tracker
"""

    def __call__(self,etype, evalue, etb):
        """Handle an exception, call for compatible with sys.excepthook"""

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
        report_name = os.path.join(rptdir,self.crash_report_fname)
        # write the report filename into the instance dict so it can get
        # properly expanded out in the user message template
        self.crash_report_fname = report_name
        TBhandler = ultraTB.VerboseTB(color_scheme=color_scheme,
                                           long_header=1)
        traceback = TBhandler.text(etype,evalue,etb,context=31)

        # print traceback to screen
        if self.show_crash_traceback:
            print >> sys.stderr, traceback

        # and generate a complete report on disk
        try:
            report = open(report_name,'w')
        except:
            print >> sys.stderr, 'Could not create crash report on disk.'
            return

        # Inform user on stderr of what happened
        msg = itpl('\n'+'*'*70+'\n'+self.user_message_template)
        print >> sys.stderr, msg

        # Construct report on disk
        report.write(self.make_report(traceback))
        report.close()
        raw_input("Press enter to exit:")

    def make_report(self,traceback):
        """Return a string containing a crash report."""

        sec_sep = '\n\n'+'*'*75+'\n\n'

        report = []
        rpt_add = report.append
        
        rpt_add('*'*75+'\n\n'+'IPython post-mortem report\n\n')
        rpt_add('IPython version: %s \n\n' % Release.version)
        rpt_add('SVN revision   : %s \n\n' % Release.revision)
        rpt_add('Platform info  : os.name -> %s, sys.platform -> %s' %
                     (os.name,sys.platform) )
        rpt_add(sec_sep+'Current user configuration structure:\n\n')
        rpt_add(pformat(self.IP.rc.dict()))
        rpt_add(sec_sep+'Crash traceback:\n\n' + traceback)
        try:
            rpt_add(sec_sep+"History of session input:")
            for line in self.IP.user_ns['_ih']:
                rpt_add(line)
            rpt_add('\n*** Last line of input (may not be in above history):\n')
            rpt_add(self.IP._last_input_line+'\n')
        except:
            pass

        return ''.join(report)

class IPythonCrashHandler(CrashHandler):
    """sys.excepthook for IPython itself, leaves a detailed report on disk."""
    
    def __init__(self,IP):

        # Set here which of the IPython authors should be listed as contact
        AUTHOR_CONTACT = 'Ville'
        
        # Set argument defaults
        app_name = 'IPython'
        bug_tracker = 'http://projects.scipy.org/ipython/ipython/report'
        contact_name,contact_email = Release.authors[AUTHOR_CONTACT][:2]
        crash_report_fname = 'IPython_crash_report.txt'
        # Call parent constructor
        CrashHandler.__init__(self,IP,app_name,contact_name,contact_email,
                              bug_tracker,crash_report_fname)

    def make_report(self,traceback):
        """Return a string containing a crash report."""

        sec_sep = '\n\n'+'*'*75+'\n\n'

        report = []
        rpt_add = report.append
        
        rpt_add('*'*75+'\n\n'+'IPython post-mortem report\n\n')
        rpt_add('IPython version: %s \n\n' % Release.version)
        rpt_add('SVN revision   : %s \n\n' % Release.revision)
        rpt_add('Platform info  : os.name -> %s, sys.platform -> %s' %
                     (os.name,sys.platform) )
        rpt_add(sec_sep+'Current user configuration structure:\n\n')
        rpt_add(pformat(self.IP.rc.dict()))
        rpt_add(sec_sep+'Crash traceback:\n\n' + traceback)
        try:
            rpt_add(sec_sep+"History of session input:")
            for line in self.IP.user_ns['_ih']:
                rpt_add(line)
            rpt_add('\n*** Last line of input (may not be in above history):\n')
            rpt_add(self.IP._last_input_line+'\n')
        except:
            pass

        return ''.join(report)
