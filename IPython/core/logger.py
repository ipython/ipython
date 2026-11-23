"""Logger class for IPython's logging facilities.
"""

#*****************************************************************************
#       Copyright (C) 2001 Janko Hauser <jhauser@zscout.de> and
#       Copyright (C) 2001-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from __future__ import annotations

#****************************************************************************
# Modules and globals

# Python standard modules
import glob
import io
import os
import time
from typing import IO

#****************************************************************************
# FIXME: This class isn't a mixin anymore, but it still needs attributes from
# ipython and does input cache management.  Finish cleanup later...

class Logger:
    """A Logfile class with different policies for file creation"""

    def __init__(self, home_dir: str, logfname: str = 'Logger.log',
                 loghead: str = '', logmode: str = 'over') -> None:

        # this is the full ipython instance, we need some attributes from it
        # which won't exist until later. What a mess, clean up later...
        self.home_dir = home_dir

        self.logfname = logfname
        self.loghead = loghead
        self.logfile: IO[str] | None = None

        # Whether to log raw or processed input
        self.log_raw_input = False

        # whether to also log output
        self.log_output = False

        # whether to put timestamps before each log entry
        self.timestamp = False

        # input filters, see logstart()
        self.skip_magics = False
        self.skip_errors = False
        self.skip_duplicates = False
        self._logged: set[str] = set()
        # Entries held back by skip_errors: (line_mod, line_ori, outputs).
        # A stack, since magics like %%capture run cells from inside a cell.
        self._pending: list[tuple[str, str, list[str]]] = []
        # Whether output belongs to an input the filters dropped.
        self._drop_output = False

        # activity control flags
        self.log_active = False

        self.logmode = logmode

    @property
    def logmode(self) -> str:
        return self._logmode

    @logmode.setter
    def logmode(self, mode: str) -> None:
        if mode not in ['append', 'backup', 'global', 'over', 'rotate']:
            raise ValueError('invalid log mode %s given' % mode)
        self._logmode = mode

    def logstart(
        self,
        logfname: str | None = None,
        loghead: str | None = None,
        logmode: str | None = None,
        log_output: bool = False,
        timestamp: bool = False,
        log_raw_input: bool = False,
        skip_magics: bool = False,
        skip_errors: bool = False,
        skip_duplicates: bool = False,
    ) -> None:
        """Generate a new log-file with a default header.

        The ``skip_*`` flags filter the input logged from now on:
        ``skip_magics`` drops input that IPython rewrites into ``get_ipython()``
        calls (magics, shell escapes, help lookups), ``skip_errors`` drops input
        that raised (the caller must report each result with ``log_pending``),
        and ``skip_duplicates`` drops input already written to this log.

        Raises RuntimeError if the log has already been started"""

        if self.logfile is not None:
            raise RuntimeError('Log file is already active: %s' %
                               self.logfname)

        # The parameters can override constructor defaults
        if logfname is not None: self.logfname = logfname
        if loghead is not None: self.loghead = loghead
        if logmode is not None: self.logmode = logmode

        # Parameters not part of the constructor
        self.timestamp = timestamp
        self.log_output = log_output
        self.log_raw_input = log_raw_input
        self.skip_magics = skip_magics
        self.skip_errors = skip_errors
        self.skip_duplicates = skip_duplicates
        self._logged = set()
        self._pending = []
        self._drop_output = False

        # init depending on the log mode requested
        isfile = os.path.isfile
        logmode = self.logmode

        if logmode == 'append':
            self.logfile = open(self.logfname, 'a', encoding='utf-8')

        elif logmode == 'backup':
            if isfile(self.logfname):
                backup_logname = self.logfname+'~'
                # Manually remove any old backup, since os.rename may fail
                # under Windows.
                if isfile(backup_logname):
                    os.remove(backup_logname)
                os.rename(self.logfname,backup_logname)
            self.logfile = open(self.logfname, 'w', encoding='utf-8')

        elif logmode == 'global':
            self.logfname = os.path.join(self.home_dir,self.logfname)
            self.logfile = open(self.logfname, 'a', encoding='utf-8')

        elif logmode == 'over':
            if isfile(self.logfname):
                os.remove(self.logfname)
            self.logfile = open(self.logfname,'w', encoding='utf-8')

        elif logmode == 'rotate':
            if isfile(self.logfname):
                if isfile(self.logfname+'.001~'):
                    old = glob.glob(self.logfname+'.*~')
                    old.sort()
                    old.reverse()
                    for f in old:
                        root, ext = os.path.splitext(f)
                        num = int(ext[1:-1])+1
                        os.rename(f, root+'.'+repr(num).zfill(3)+'~')
                os.rename(self.logfname, self.logfname+'.001~')
            self.logfile = open(self.logfname, 'w', encoding='utf-8')

        if logmode != 'append':
            self.logfile.write(self.loghead)

        self.logfile.flush()
        self.log_active = True

    def switch_log(self, val: bool) -> None:
        """Switch logging on/off. val should be ONLY a boolean."""

        if val not in [False,True,0,1]:
            raise ValueError('Call switch_log ONLY with a boolean argument, '
                             'not with: %s' % val)

        label = {0:'OFF',1:'ON',False:'OFF',True:'ON'}

        if self.logfile is None:
            print("""
Logging hasn't been started yet (use logstart for that).

%logon/%logoff are for temporarily starting and stopping logging for a logfile
which already exists. But you must first start the logging process with
%logstart (optionally giving a logfile name).""")

        else:
            if self.log_active == val:
                print('Logging is already',label[val])
            else:
                print('Switching logging',label[val])
                self.log_active = not self.log_active
                self.log_active_out = self.log_active

    def logstate(self) -> None:
        """Print a status message about the logger."""
        if self.logfile is None:
            print('Logging has not been activated.')
        else:
            state = self.log_active and "active" or "temporarily suspended"
            print("Filename       :", self.logfname)
            print("Mode           :", self.logmode)
            print("Output logging :", self.log_output)
            print("Raw input log  :", self.log_raw_input)
            print("Timestamping   :", self.timestamp)
            print("Skip magics    :", self.skip_magics)
            print("Skip errors    :", self.skip_errors)
            print("Skip duplicates:", self.skip_duplicates)
            print("State          :", state)

    def log(self, line_mod: str, line_ori: str) -> None:
        """Write the sources to a log.

        Inputs:

        - line_mod: possibly modified input, such as the transformations made
          by input prefilters or input handlers of various kinds. This should
          always be valid Python.

        - line_ori: unmodified input line from the user. This is not
          necessarily valid Python.
        """

        if self.skip_errors:
            # Written or dropped by log_pending once the result is known.
            self._pending.append((line_mod, line_ori, []))
        else:
            self.log_input(line_mod, line_ori)

    def log_input(self, line_mod: str, line_ori: str) -> bool:
        """Write one input entry now, honoring the skip filters.

        Returns whether the entry was written. Output logged after a dropped
        entry is dropped with it."""
        # Write the log line, but decide which one according to the
        # log_raw_input flag, set when the log is started.
        data = line_ori if self.log_raw_input else line_mod
        written = bool(self.log_active and data)
        if self.skip_magics and "get_ipython()." in line_mod:
            written = False
        if self.skip_duplicates and data in self._logged:
            written = False
        self._drop_output = not written
        if written:
            if self.skip_duplicates:
                self._logged.add(data)
            self.log_write(data)
        return written

    def log_pending(self, success: bool) -> None:
        """Write the input held back by ``skip_errors`` if it succeeded."""
        if not self._pending:
            return
        line_mod, line_ori, outputs = self._pending.pop()
        if success and self.log_input(line_mod, line_ori):
            for output in outputs:
                self.log_write(output, "output")

    def log_write(self, data: str, kind: str = 'input') -> None:
        """Write data to the log file, if active"""

        if kind == "output":
            if self._pending:
                # Held until the input it belongs to is written or dropped.
                self._pending[-1][2].append(data)
                return
            if self._drop_output:
                return
        # print('data: %r' % data)  # dbg
        if self.log_active and data:
            write = self.logfile.write
            if kind=='input':
                if self.timestamp:
                    write(time.strftime('# %a, %d %b %Y %H:%M:%S\n', time.localtime()))
                write(data)
            elif kind=='output' and self.log_output:
                odata = '\n'.join(['#[Out]# %s' % s
                                   for s in data.splitlines()])
                write('%s\n' % odata)
            try:
                self.logfile.flush()
            except OSError:
                print("Failed to flush the log file.")
                print(
                    f"Please check that {self.logfname} exists and have the right permissions."
                )
                print(
                    "Also consider turning off the log with `%logstop` to avoid this warning."
                )

    def logstop(self) -> None:
        """Fully stop logging and close log file.

        In order to start logging again, a new logstart() call needs to be
        made, possibly (though not necessarily) with a new filename, mode and
        other options."""

        if self.logfile is not None:
            self.logfile.close()
            self.logfile = None
        else:
            print("Logging hadn't been started.")
        self.log_active = False
        self.skip_magics = self.skip_errors = self.skip_duplicates = False
        self._pending = []
        self._drop_output = False

    # For backwards compatibility, in case anyone was using this.
    close_log = logstop
