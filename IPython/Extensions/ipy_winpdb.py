""" Debug a script (like %run -d) in IPython process, Using WinPdb

Usage:

%wdb test.py
    run test.py, with a winpdb breakpoint at start of the file 
    
%wdb pass
    Change the password (e.g. if you have forgotten the old one)
"""

import os

import IPython.ipapi
import rpdb2

ip = IPython.ipapi.get()

rpdb_started = False

def wdb_f(self, arg):
    """ Debug a script (like %run -d) in IPython process, Using WinPdb
    
    Usage:
    
    %wdb test.py
        run test.py, with a winpdb breakpoint at start of the file 
        
    %wdb pass
        Change the password (e.g. if you have forgotten the old one)
        
    Note that after the script has been run, you need to do "Go" (f5) 
    in WinPdb to resume normal IPython operation.
    """

    global rpdb_started
    if not arg.strip():
        print __doc__
        return
        
    if arg.strip() == 'pass':
        passwd = raw_input('Enter new winpdb session password: ')
        ip.db['winpdb_pass'] = passwd
        print "Winpdb password changed"
        if rpdb_started:
            print "You need to restart IPython to use the new password"
        return 
    
    path = os.path.abspath(arg)
    if not os.path.isfile(path):
        raise IPython.ipapi.UsageError("%%wdb: file %s does not exist" % path)
    if not rpdb_started:
        passwd = ip.db.get('winpdb_pass', None)
        if passwd is None:
            import textwrap
            print textwrap.dedent("""\
            Winpdb sessions need a password that you use for attaching the external
            winpdb session. IPython will remember this. You can change the password later 
            by '%wpdb pass'
            """)
            passwd = raw_input('Enter new winpdb session password: ')
            ip.db['winpdb_pass'] = passwd
            
        print "Starting rpdb2 in IPython process"
        rpdb2.start_embedded_debugger(passwd, timeout = 0)
        rpdb_started = True
        
    rpdb2.set_temp_breakpoint(path)
    print 'It is time to attach with WinPdb (launch WinPdb if needed, File -> Attach)'
    ip.magic('%run ' + arg)
    

ip.expose_magic('wdb', wdb_f)
