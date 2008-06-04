# -*- coding: utf-8 -*-
"""
IPython -- An enhanced Interactive Python

Requires Python 2.1 or better.

This file contains the main make_IPython() starter function.

$Id: ipmaker.py 2930 2008-01-11 07:03:11Z vivainio $"""

#*****************************************************************************
#       Copyright (C) 2001-2006 Fernando Perez. <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license
__version__ = Release.version

try:
    credits._Printer__data = """
    Python: %s

    IPython: Fernando Perez, Janko Hauser, Nathan Gray, and many users.
    See http://ipython.scipy.org for more information.""" \
    % credits._Printer__data

    copyright._Printer__data += """

    Copyright (c) 2001-2004 Fernando Perez, Janko Hauser, Nathan Gray.
    All Rights Reserved."""
except NameError:
    # Can happen if ipython was started with 'python -S', so that site.py is
    # not loaded
    pass

#****************************************************************************
# Required modules

# From the standard library
import __main__
import __builtin__
import os
import re
import sys
import types
from pprint import pprint,pformat

# Our own
from IPython import DPyGetOpt
from IPython.ipstruct import Struct
from IPython.OutputTrap import OutputTrap
from IPython.ConfigLoader import ConfigLoader
from IPython.iplib import InteractiveShell
from IPython.usage import cmd_line_usage,interactive_usage
from IPython.genutils import *

def force_import(modname):
    if modname in sys.modules:
        print "reload",modname
        reload(sys.modules[modname])
    else:
        __import__(modname)
        

#-----------------------------------------------------------------------------
def make_IPython(argv=None,user_ns=None,user_global_ns=None,debug=1,
                 rc_override=None,shell_class=InteractiveShell,
                 embedded=False,**kw):
    """This is a dump of IPython into a single function.

    Later it will have to be broken up in a sensible manner.

    Arguments:

    - argv: a list similar to sys.argv[1:].  It should NOT contain the desired
    script name, b/c DPyGetOpt strips the first argument only for the real
    sys.argv.

    - user_ns: a dict to be used as the user's namespace."""

    #----------------------------------------------------------------------
    # Defaults and initialization
    
    # For developer debugging, deactivates crash handler and uses pdb.
    DEVDEBUG = False

    if argv is None:
        argv = sys.argv

    # __IP is the main global that lives throughout and represents the whole
    # application. If the user redefines it, all bets are off as to what
    # happens.

    # __IP is the name of he global which the caller will have accessible as
    # __IP.name. We set its name via the first parameter passed to
    # InteractiveShell:

    IP = shell_class('__IP',user_ns=user_ns,user_global_ns=user_global_ns,
                     embedded=embedded,**kw)

    # Put 'help' in the user namespace
    try:
        from site import _Helper
        IP.user_ns['help'] = _Helper()
    except ImportError:
        warn('help() not available - check site.py')
    IP.user_config_ns = {}


    if DEVDEBUG:
        # For developer debugging only (global flag)
        from IPython import ultraTB
        sys.excepthook = ultraTB.VerboseTB(call_pdb=1)

    IP.BANNER_PARTS = ['Python %s\n'
                         'Type "copyright", "credits" or "license" '
                         'for more information.\n'
                         % (sys.version.split('\n')[0],),
                         "IPython %s -- An enhanced Interactive Python."
                         % (__version__,),
"""\
?         -> Introduction and overview of IPython's features.
%quickref -> Quick reference.
help      -> Python's own help system.
object?   -> Details about 'object'. ?object also works, ?? prints more.
""" ]

    IP.usage = interactive_usage

    # Platform-dependent suffix and directory names.  We use _ipython instead
    # of .ipython under win32 b/c there's software that breaks with .named
    # directories on that platform.
    if os.name == 'posix':
        rc_suffix = ''
        ipdir_def = '.ipython'
    else:
        rc_suffix = '.ini'
        ipdir_def = '_ipython'

    # default directory for configuration
    ipythondir_def = os.path.abspath(os.environ.get('IPYTHONDIR',
                                 os.path.join(IP.home_dir,ipdir_def)))

    sys.path.insert(0, '') # add . to sys.path. Fix from Prabhu Ramachandran

    # we need the directory where IPython itself is installed
    import IPython
    IPython_dir = os.path.dirname(IPython.__file__)
    del IPython
    
    #-------------------------------------------------------------------------
    # Command line handling

    # Valid command line options (uses DPyGetOpt syntax, like Perl's
    # GetOpt::Long)

    # Any key not listed here gets deleted even if in the file (like session
    # or profile). That's deliberate, to maintain the rc namespace clean.

    # Each set of options appears twice: under _conv only the names are
    # listed, indicating which type they must be converted to when reading the
    # ipythonrc file. And under DPyGetOpt they are listed with the regular
    # DPyGetOpt syntax (=s,=i,:f,etc).

    # Make sure there's a space before each end of line (they get auto-joined!)
    cmdline_opts = ('autocall=i autoindent! automagic! banner! cache_size|cs=i '
                    'c=s classic|cl color_info! colors=s confirm_exit! '
                    'debug! deep_reload! editor=s log|l messages! nosep '
                    'object_info_string_level=i pdb! '
                    'pprint! prompt_in1|pi1=s prompt_in2|pi2=s prompt_out|po=s '
                    'pydb! '
                    'pylab_import_all! '
                    'quick screen_length|sl=i prompts_pad_left=i '
                    'logfile|lf=s logplay|lp=s profile|p=s '
                    'readline! readline_merge_completions! '
                    'readline_omit__names! '
                    'rcfile=s separate_in|si=s separate_out|so=s '
                    'separate_out2|so2=s xmode=s wildcards_case_sensitive! '
                    'magic_docstrings system_verbose! '
                    'multi_line_specials! '
                    'term_title! wxversion=s '
                    'autoedit_syntax!')

    # Options that can *only* appear at the cmd line (not in rcfiles).
    
    cmdline_only = ('help interact|i ipythondir=s Version upgrade '
                    'gthread! qthread! q4thread! wthread! tkthread! pylab! tk! '
                    # 'twisted!'  # disabled for now.
                    )

    # Build the actual name list to be used by DPyGetOpt
    opts_names = qw(cmdline_opts) + qw(cmdline_only)

    # Set sensible command line defaults.
    # This should have everything from  cmdline_opts and cmdline_only
    opts_def = Struct(autocall = 1,
                      autoedit_syntax = 0,
                      autoindent = 0,
                      automagic = 1,
                      autoexec = [],
                      banner = 1,
                      c = '',
                      cache_size = 1000,
                      classic = 0,
                      color_info = 0,
                      colors = 'NoColor',
                      confirm_exit = 1,
                      debug = 0,
                      deep_reload = 0,
                      editor = '0',
                      gthread = 0,
                      help = 0,
                      interact = 0,
                      ipythondir = ipythondir_def,
                      log = 0,
                      logfile = '',
                      logplay = '',
                      messages = 1,
                      multi_line_specials = 1,
                      nosep = 0,
                      object_info_string_level = 0,
                      pdb = 0,
                      pprint = 0,
                      profile = '',
                      prompt_in1 = 'In [\\#]: ',
                      prompt_in2 = '   .\\D.: ',
                      prompt_out = 'Out[\\#]: ',
                      prompts_pad_left = 1,
                      pydb = 0,
                      pylab = 0,
                      pylab_import_all = 1,
                      q4thread = 0,
                      qthread = 0,
                      quick = 0,
                      quiet = 0,
                      rcfile = 'ipythonrc' + rc_suffix,
                      readline = 1,
                      readline_merge_completions = 1,
                      readline_omit__names = 0,
                      screen_length = 0,
                      separate_in = '\n',
                      separate_out = '\n',
                      separate_out2 = '',
                      system_header = 'IPython system call: ',
                      system_verbose = 0,
                      term_title = 1,
                      tk = 0,
                      #twisted= 0,  # disabled for now
                      upgrade = 0,
                      Version = 0,
                      wildcards_case_sensitive = 1,
                      wthread = 0,
                      wxversion = '0',
                      xmode = 'Context',
                      magic_docstrings = 0,  # undocumented, for doc generation
                      )
    
    # Things that will *only* appear in rcfiles (not at the command line).
    # Make sure there's a space before each end of line (they get auto-joined!)
    rcfile_opts = { qwflat: 'include import_mod import_all execfile ',
                    qw_lol: 'import_some ',
                    # for things with embedded whitespace:
                    list_strings:'execute alias readline_parse_and_bind ',
                    # Regular strings need no conversion:
                    None:'readline_remove_delims ',
                    }
    # Default values for these
    rc_def = Struct(include = [],
                    import_mod = [], 
                    import_all = [],
                    import_some = [[]],
                    execute = [],
                    execfile = [],
                    alias = [],
                    readline_parse_and_bind = [],
                    readline_remove_delims = '',
                    )

    # Build the type conversion dictionary from the above tables:
    typeconv = rcfile_opts.copy()
    typeconv.update(optstr2types(cmdline_opts))

    # FIXME: the None key appears in both, put that back together by hand. Ugly!
    typeconv[None] += ' ' + rcfile_opts[None]

    # Remove quotes at ends of all strings (used to protect spaces)
    typeconv[unquote_ends] = typeconv[None]
    del typeconv[None]

    # Build the list we'll use to make all config decisions with defaults:
    opts_all = opts_def.copy()
    opts_all.update(rc_def)

    # Build conflict resolver for recursive loading of config files:
    # - preserve means the outermost file maintains the value, it is not
    # overwritten if an included file has the same key.
    # - add_flip applies + to the two values, so it better make sense to add
    # those types of keys. But it flips them first so that things loaded
    # deeper in the inclusion chain have lower precedence.
    conflict = {'preserve': ' '.join([ typeconv[int],
                                       typeconv[unquote_ends] ]),
                'add_flip': ' '.join([ typeconv[qwflat],
                                       typeconv[qw_lol],
                                       typeconv[list_strings] ])
                }

    # Now actually process the command line
    getopt = DPyGetOpt.DPyGetOpt()
    getopt.setIgnoreCase(0)

    getopt.parseConfiguration(opts_names)

    try:
        getopt.processArguments(argv)
    except DPyGetOpt.ArgumentError, exc:
        print cmd_line_usage
        warn('\nError in Arguments: "%s"' % exc)
        sys.exit(1)

    # convert the options dict to a struct for much lighter syntax later
    opts = Struct(getopt.optionValues)
    args = getopt.freeValues

    # this is the struct (which has default values at this point) with which
    # we make all decisions:
    opts_all.update(opts)

    # Options that force an immediate exit
    if opts_all.help:
        page(cmd_line_usage)
        sys.exit()

    if opts_all.Version:
        print __version__
        sys.exit()

    if opts_all.magic_docstrings:
        IP.magic_magic('-latex')
        sys.exit()

    # add personal ipythondir to sys.path so that users can put things in
    # there for customization
    sys.path.append(os.path.abspath(opts_all.ipythondir))

    # Create user config directory if it doesn't exist. This must be done
    # *after* getting the cmd line options.
    if not os.path.isdir(opts_all.ipythondir):
        IP.user_setup(opts_all.ipythondir,rc_suffix,'install')

    # upgrade user config files while preserving a copy of the originals
    if opts_all.upgrade:
        IP.user_setup(opts_all.ipythondir,rc_suffix,'upgrade')

    # check mutually exclusive options in the *original* command line
    mutex_opts(opts,[qw('log logfile'),qw('rcfile profile'),
                     qw('classic profile'),qw('classic rcfile')])

    #---------------------------------------------------------------------------
    # Log replay
    
    # if -logplay, we need to 'become' the other session. That basically means
    # replacing the current command line environment with that of the old
    # session and moving on.

    # this is needed so that later we know we're in session reload mode, as
    # opts_all will get overwritten:
    load_logplay = 0

    if opts_all.logplay:
        load_logplay = opts_all.logplay 
        opts_debug_save = opts_all.debug
        try:
            logplay = open(opts_all.logplay)
        except IOError:
            if opts_all.debug: IP.InteractiveTB()
            warn('Could not open logplay file '+`opts_all.logplay`)
            # restore state as if nothing had happened and move on, but make
            # sure that later we don't try to actually load the session file
            logplay = None
            load_logplay = 0
            del opts_all.logplay
        else:
            try: 
                logplay.readline()
                logplay.readline();
                # this reloads that session's command line
                cmd = logplay.readline()[6:] 
                exec cmd
                # restore the true debug flag given so that the process of
                # session loading itself can be monitored.
                opts.debug = opts_debug_save
                # save the logplay flag so later we don't overwrite the log
                opts.logplay = load_logplay
                # now we must update our own structure with defaults
                opts_all.update(opts)
                # now load args
                cmd = logplay.readline()[6:] 
                exec cmd
                logplay.close()
            except:
                logplay.close()
                if opts_all.debug: IP.InteractiveTB()
                warn("Logplay file lacking full configuration information.\n"
                     "I'll try to read it, but some things may not work.")

    #-------------------------------------------------------------------------
    # set up output traps: catch all output from files, being run, modules
    # loaded, etc. Then give it to the user in a clean form at the end.
    
    msg_out = 'Output messages. '
    msg_err = 'Error messages. '
    msg_sep = '\n'
    msg = Struct(config    = OutputTrap('Configuration Loader',msg_out,
                                        msg_err,msg_sep,debug,
                                        quiet_out=1),
                 user_exec = OutputTrap('User File Execution',msg_out,
                                        msg_err,msg_sep,debug),
                 logplay   = OutputTrap('Log Loader',msg_out,
                                        msg_err,msg_sep,debug),
                 summary = ''
                 )

    #-------------------------------------------------------------------------
    # Process user ipythonrc-type configuration files

    # turn on output trapping and log to msg.config
    # remember that with debug on, trapping is actually disabled
    msg.config.trap_all()

    # look for rcfile in current or default directory
    try:
        opts_all.rcfile = filefind(opts_all.rcfile,opts_all.ipythondir)
    except IOError:
        if opts_all.debug:  IP.InteractiveTB()
        warn('Configuration file %s not found. Ignoring request.'
             % (opts_all.rcfile) )

    # 'profiles' are a shorthand notation for config filenames
    profile_handled_by_legacy = False
    if opts_all.profile:
            
        try:
            opts_all.rcfile = filefind('ipythonrc-' + opts_all.profile
                                       + rc_suffix,
                                       opts_all.ipythondir)
            profile_handled_by_legacy = True
        except IOError:
           if opts_all.debug:  IP.InteractiveTB()
           opts.profile = ''  # remove profile from options if invalid
           # We won't warn anymore, primary method is ipy_profile_PROFNAME
           # which does trigger a warning.

    # load the config file
    rcfiledata = None
    if opts_all.quick:
        print 'Launching IPython in quick mode. No config file read.'
    elif opts_all.rcfile:
        try:
            cfg_loader = ConfigLoader(conflict)
            rcfiledata = cfg_loader.load(opts_all.rcfile,typeconv,
                                         'include',opts_all.ipythondir,
                                         purge = 1,
                                         unique = conflict['preserve'])
        except:
            IP.InteractiveTB()
            warn('Problems loading configuration file '+
                 `opts_all.rcfile`+
                 '\nStarting with default -bare bones- configuration.')
    else:
        warn('No valid configuration file found in either currrent directory\n'+
             'or in the IPython config. directory: '+`opts_all.ipythondir`+
             '\nProceeding with internal defaults.')

    #------------------------------------------------------------------------
    # Set exception handlers in mode requested by user.
    otrap = OutputTrap(trap_out=1)  # trap messages from magic_xmode
    IP.magic_xmode(opts_all.xmode)
    otrap.release_out()

    #------------------------------------------------------------------------
    # Execute user config

    # Create a valid config structure with the right precedence order:
    # defaults < rcfile < command line.  This needs to be in the instance, so
    # that method calls below that rely on it find it.
    IP.rc = rc_def.copy()

    # Work with a local alias inside this routine to avoid unnecessary
    # attribute lookups.
    IP_rc = IP.rc
    
    IP_rc.update(opts_def)
    if rcfiledata:
        # now we can update 
        IP_rc.update(rcfiledata)
    IP_rc.update(opts)
    IP_rc.update(rc_override)

    # Store the original cmd line for reference:
    IP_rc.opts = opts
    IP_rc.args = args

    # create a *runtime* Struct like rc for holding parameters which may be
    # created and/or modified by runtime user extensions.
    IP.runtime_rc = Struct()

    # from this point on, all config should be handled through IP_rc,
    # opts* shouldn't be used anymore.

    
    # update IP_rc with some special things that need manual
    # tweaks. Basically options which affect other options. I guess this
    # should just be written so that options are fully orthogonal and we
    # wouldn't worry about this stuff!

    if IP_rc.classic:
        IP_rc.quick = 1
        IP_rc.cache_size = 0
        IP_rc.pprint = 0
        IP_rc.prompt_in1 = '>>> '
        IP_rc.prompt_in2 = '... '
        IP_rc.prompt_out = ''
        IP_rc.separate_in = IP_rc.separate_out = IP_rc.separate_out2 = '0'
        IP_rc.colors = 'NoColor'
        IP_rc.xmode = 'Plain'

    IP.pre_config_initialization()
    # configure readline

    # update exception handlers with rc file status
    otrap.trap_out()  # I don't want these messages ever.
    IP.magic_xmode(IP_rc.xmode)
    otrap.release_out()

    # activate logging if requested and not reloading a log
    if IP_rc.logplay:
        IP.magic_logstart(IP_rc.logplay + ' append')
    elif  IP_rc.logfile:
        IP.magic_logstart(IP_rc.logfile)
    elif IP_rc.log:
        IP.magic_logstart()

    # find user editor so that it we don't have to look it up constantly
    if IP_rc.editor.strip()=='0':
        try:
            ed = os.environ['EDITOR']
        except KeyError:
            if os.name == 'posix':
                ed = 'vi'  # the only one guaranteed to be there!
            else:
                ed = 'notepad' # same in Windows!
        IP_rc.editor = ed

    # Keep track of whether this is an embedded instance or not (useful for
    # post-mortems).
    IP_rc.embedded = IP.embedded

    # Recursive reload
    try:
        from IPython import deep_reload
        if IP_rc.deep_reload:
            __builtin__.reload = deep_reload.reload
        else:
            __builtin__.dreload = deep_reload.reload
        del deep_reload
    except ImportError:
        pass

    # Save the current state of our namespace so that the interactive shell
    # can later know which variables have been created by us from config files
    # and loading. This way, loading a file (in any way) is treated just like
    # defining things on the command line, and %who works as expected.

    # DON'T do anything that affects the namespace beyond this point!
    IP.internal_ns.update(__main__.__dict__)

    #IP.internal_ns.update(locals()) # so our stuff doesn't show up in %who

    # Now run through the different sections of the users's config
    if IP_rc.debug:    
        print 'Trying to execute the following configuration structure:'
        print '(Things listed first are deeper in the inclusion tree and get'
        print 'loaded first).\n'
        pprint(IP_rc.__dict__)
        
    for mod in IP_rc.import_mod:
        try:
            exec 'import '+mod in IP.user_ns
        except :
            IP.InteractiveTB()
            import_fail_info(mod)

    for mod_fn in IP_rc.import_some:
        if not mod_fn == []: 
            mod,fn = mod_fn[0],','.join(mod_fn[1:])
            try:
                exec 'from '+mod+' import '+fn in IP.user_ns
            except :
                IP.InteractiveTB()
                import_fail_info(mod,fn)

    for mod in IP_rc.import_all:
        try:
            exec 'from '+mod+' import *' in IP.user_ns
        except :
            IP.InteractiveTB()
            import_fail_info(mod)

    for code in IP_rc.execute:
        try:
            exec code in IP.user_ns
        except:
            IP.InteractiveTB()
            warn('Failure executing code: ' + `code`)

    # Execute the files the user wants in ipythonrc
    for file in IP_rc.execfile:
        try:
            file = filefind(file,sys.path+[IPython_dir])
        except IOError:
            warn(itpl('File $file not found. Skipping it.'))
        else:
            IP.safe_execfile(os.path.expanduser(file),IP.user_ns)

    # finally, try importing ipy_*_conf for final configuration
    try:
        import ipy_system_conf
    except ImportError:
        if opts_all.debug:  IP.InteractiveTB()
        warn("Could not import 'ipy_system_conf'")        
    except:
        IP.InteractiveTB()
        import_fail_info('ipy_system_conf')
        
    # only import prof module if ipythonrc-PROF was not found
    if opts_all.profile and not profile_handled_by_legacy:
        profmodname = 'ipy_profile_' + opts_all.profile
        try:
            
            force_import(profmodname)
        except:
            IP.InteractiveTB()
            print "Error importing",profmodname,"- perhaps you should run %upgrade?"
            import_fail_info(profmodname)
        else:
            opts.profile = opts_all.profile
    else:
        force_import('ipy_profile_none')
    try:
            
        force_import('ipy_user_conf')
        
    except:
        conf = opts_all.ipythondir + "/ipy_user_conf.py"
        IP.InteractiveTB()
        if not os.path.isfile(conf):
            warn(conf + ' does not exist, please run %upgrade!')

        import_fail_info("ipy_user_conf")

    # Define the history file for saving commands in between sessions
    try:
        histfname = 'history-%s' % opts.profile
    except AttributeError:
        histfname = 'history'
    IP.histfile = os.path.join(opts_all.ipythondir,histfname)

    # finally, push the argv to options again to ensure highest priority
    IP_rc.update(opts)
    
    # release stdout and stderr and save config log into a global summary
    msg.config.release_all()
    if IP_rc.messages:
        msg.summary += msg.config.summary_all()

    #------------------------------------------------------------------------
    # Setup interactive session

    # Now we should be fully configured. We can then execute files or load
    # things only needed for interactive use. Then we'll open the shell.

    # Take a snapshot of the user namespace before opening the shell. That way
    # we'll be able to identify which things were interactively defined and
    # which were defined through config files.
    IP.user_config_ns.update(IP.user_ns)

    # Force reading a file as if it were a session log. Slower but safer.
    if load_logplay:
        print 'Replaying log...'
        try:
            if IP_rc.debug:
                logplay_quiet = 0
            else:
                 logplay_quiet = 1

            msg.logplay.trap_all()
            IP.safe_execfile(load_logplay,IP.user_ns,
                             islog = 1, quiet = logplay_quiet)
            msg.logplay.release_all()
            if IP_rc.messages:
                msg.summary += msg.logplay.summary_all()
        except:
            warn('Problems replaying logfile %s.' % load_logplay)
            IP.InteractiveTB()

    # Load remaining files in command line
    msg.user_exec.trap_all()

    # Do NOT execute files named in the command line as scripts to be loaded
    # by embedded instances.  Doing so has the potential for an infinite
    # recursion if there are exceptions thrown in the process.

    # XXX FIXME: the execution of user files should be moved out to after
    # ipython is fully initialized, just as if they were run via %run at the
    # ipython prompt.  This would also give them the benefit of ipython's
    # nice tracebacks.

    if (not embedded and IP_rc.args and 
        not IP_rc.args[0].lower().endswith('.ipy')):
        name_save = IP.user_ns['__name__']
        IP.user_ns['__name__'] = '__main__'
        # Set our own excepthook in case the user code tries to call it
        # directly. This prevents triggering the IPython crash handler.
        old_excepthook,sys.excepthook = sys.excepthook, IP.excepthook

        save_argv = sys.argv[1:] # save it for later restoring
        
        sys.argv = args
        
        try:
            IP.safe_execfile(args[0], IP.user_ns)
        finally:
            # Reset our crash handler in place
            sys.excepthook = old_excepthook
            sys.argv[:] = save_argv
            IP.user_ns['__name__'] = name_save
        
    msg.user_exec.release_all()

    if IP_rc.messages:
        msg.summary += msg.user_exec.summary_all()

    # since we can't specify a null string on the cmd line, 0 is the equivalent:
    if IP_rc.nosep:
        IP_rc.separate_in = IP_rc.separate_out = IP_rc.separate_out2 = '0'
    if IP_rc.separate_in == '0': IP_rc.separate_in = ''
    if IP_rc.separate_out == '0': IP_rc.separate_out = ''
    if IP_rc.separate_out2 == '0': IP_rc.separate_out2 = ''
    IP_rc.separate_in = IP_rc.separate_in.replace('\\n','\n')
    IP_rc.separate_out = IP_rc.separate_out.replace('\\n','\n')
    IP_rc.separate_out2 = IP_rc.separate_out2.replace('\\n','\n')

    # Determine how many lines at the bottom of the screen are needed for
    # showing prompts, so we can know wheter long strings are to be printed or
    # paged:
    num_lines_bot = IP_rc.separate_in.count('\n')+1
    IP_rc.screen_length = IP_rc.screen_length - num_lines_bot

    # configure startup banner
    if IP_rc.c:  # regular python doesn't print the banner with -c
        IP_rc.banner = 0
    if IP_rc.banner:
        BANN_P = IP.BANNER_PARTS
    else:
        BANN_P = []

    if IP_rc.profile: BANN_P.append('IPython profile: %s\n' % IP_rc.profile)

    # add message log (possibly empty)
    if msg.summary: BANN_P.append(msg.summary)
    # Final banner is a string
    IP.BANNER = '\n'.join(BANN_P)

    # Finalize the IPython instance.  This assumes the rc structure is fully
    # in place.
    IP.post_config_initialization()

    return IP
#************************ end of file <ipmaker.py> **************************
