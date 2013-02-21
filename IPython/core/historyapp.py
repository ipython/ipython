# encoding: utf-8
"""
An application for managing IPython history.

To be invoked as the `ipython history` subcommand.
"""
from __future__ import print_function

import os
import sqlite3

from IPython.config.application import Application
from IPython.core.application import BaseIPythonApplication
from IPython.utils.traitlets import Bool, Int, Dict

trim_hist_help = """Trim the IPython history database to the last 1000 entries.

This actually copies the last 1000 entries to a new database, and then replaces
the old file with the new.
"""

class HistoryTrim(BaseIPythonApplication):
    description = trim_hist_help
    
    backup = Bool(False, config=True,
        help="Keep the old history file as history.sqlite.<N>")
    
    keep = Int(1000, config=True,
        help="Number of recent lines to keep in the database.")
    
    flags = Dict(dict(
        backup = ({'HistoryTrim' : {'backup' : True}},
            "Set Application.log_level to 0, maximizing log output."
        )
    ))
    
    def start(self):
        profile_dir = self.profile_dir.location
        hist_file = os.path.join(profile_dir, 'history.sqlite')
        con = sqlite3.connect(hist_file)

        # Grab the recent history from the current database.
        inputs = list(con.execute('SELECT session, line, source, source_raw FROM '
                                'history ORDER BY session DESC, line DESC LIMIT ?', (self.keep+1,)))
        if len(inputs) <= self.keep:
            print("There are already at most %d entries in the history database." % self.keep)
            print("Not doing anything.")
            return
        
        print("Trimming history to the most recent %d entries." % self.keep)
        
        inputs.pop() # Remove the extra element we got to check the length.
        inputs.reverse()
        first_session = inputs[0][0]
        outputs = list(con.execute('SELECT session, line, output FROM '
                                   'output_history WHERE session >= ?', (first_session,)))
        sessions = list(con.execute('SELECT session, start, end, num_cmds, remark FROM '
                                    'sessions WHERE session >= ?', (first_session,)))
        con.close()
        
        # Create the new history database.
        new_hist_file = os.path.join(profile_dir, 'history.sqlite.new')
        i = 0
        while os.path.exists(new_hist_file):
            # Make sure we don't interfere with an existing file.
            i += 1
            new_hist_file = os.path.join(profile_dir, 'history.sqlite.new'+str(i))
        new_db = sqlite3.connect(new_hist_file)
        new_db.execute("""CREATE TABLE IF NOT EXISTS sessions (session integer
                            primary key autoincrement, start timestamp,
                            end timestamp, num_cmds integer, remark text)""")
        new_db.execute("""CREATE TABLE IF NOT EXISTS history
                        (session integer, line integer, source text, source_raw text,
                        PRIMARY KEY (session, line))""")
        new_db.execute("""CREATE TABLE IF NOT EXISTS output_history
                        (session integer, line integer, output text,
                        PRIMARY KEY (session, line))""")
        new_db.commit()


        with new_db:
            # Add the recent history into the new database.
            new_db.executemany('insert into sessions values (?,?,?,?,?)', sessions)
            new_db.executemany('insert into history values (?,?,?,?)', inputs)
            new_db.executemany('insert into output_history values (?,?,?)', outputs)
        new_db.close()

        if self.backup:
            i = 1
            backup_hist_file = os.path.join(profile_dir, 'history.sqlite.old.%d' % i)
            while os.path.exists(backup_hist_file):
                i += 1
                backup_hist_file = os.path.join(profile_dir, 'history.sqlite.old.%d' % i)
            os.rename(hist_file, backup_hist_file)
            print("Backed up longer history file to", backup_hist_file)
        else:
            os.remove(hist_file)
        
        os.rename(new_hist_file, hist_file)


class HistoryApp(Application):
    name = u'ipython-history'
    description = "Manage the IPython history database."

    subcommands = Dict(dict(
        trim = (HistoryTrim, HistoryTrim.description.splitlines()[0]),
    ))

    def start(self):
        if self.subapp is None:
            print("No subcommand specified. Must specify one of: %s" % \
                                                    (self.subcommands.keys()))
            print()
            self.print_description()
            self.print_subcommands()
            self.exit(1)
        else:
            return self.subapp.start()
