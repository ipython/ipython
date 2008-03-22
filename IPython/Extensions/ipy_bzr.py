""" Extension for bzr command tab completer. Supports comlpeting commands and options

Unlike the core IPython, you should note that this extension is under GPL, not BSD.

Based on "shell" bzr plugin by Aaron Bentley, license is below. The IPython additions
are at the bottom of the file, the rest is left untouched.

Must be loaded with ip.load('ipy_bzr') 

""" 

# Copyright (C) 2004, 2005 Aaron Bentley
# <aaron@aaronbentley.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import cmd
from itertools import chain
import os
import shlex
import stat
import string
import sys

from bzrlib import osutils
from bzrlib.branch import Branch
from bzrlib.config import config_dir, ensure_config_dir_exists
from bzrlib.commands import get_cmd_object, get_all_cmds, get_alias
from bzrlib.errors import BzrError
from bzrlib.workingtree import WorkingTree
import bzrlib.plugin


SHELL_BLACKLIST = set(['rm', 'ls'])
COMPLETION_BLACKLIST = set(['shell'])


class BlackListedCommand(BzrError):
    def __init__(self, command):
        BzrError.__init__(self, "The command %s is blacklisted for shell use" %
                          command)


class CompletionContext(object):
    def __init__(self, text, command=None, prev_opt=None, arg_pos=None):
        self.text = text
        self.command = command
        self.prev_opt = prev_opt
        self.arg_pos = None

    def get_completions(self):
        try:
            return self.get_completions_or_raise()
        except Exception, e:
            print e, type(e)
            return []

    def get_option_completions(self):
        try:
            command_obj = get_cmd_object(self.command)
        except BzrError:
            return []
        opts = [o+" " for o in iter_opt_completions(command_obj)]
        return list(filter_completions(opts, self.text))

    def get_completions_or_raise(self):
        if self.command is None:
            if '/' in self.text:
                iter = iter_executables(self.text)
            else:
                iter = (c+" " for c in iter_command_names() if
                        c not in COMPLETION_BLACKLIST)
            return list(filter_completions(iter, self.text))
        if self.prev_opt is None:
            completions = self.get_option_completions()
            if self.command == "cd":
                iter = iter_dir_completions(self.text)
                completions.extend(list(filter_completions(iter, self.text)))
            else:
                iter = iter_file_completions(self.text)
                completions.extend(filter_completions(iter, self.text))
            return completions


class PromptCmd(cmd.Cmd):

    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "bzr> "
        try:
            self.tree = WorkingTree.open_containing('.')[0]
        except:
            self.tree = None
        self.set_title()
        self.set_prompt()
        self.identchars += '-'
        ensure_config_dir_exists()
        self.history_file = osutils.pathjoin(config_dir(), 'shell-history')
        readline.set_completer_delims(string.whitespace)
        if os.access(self.history_file, os.R_OK) and \
            os.path.isfile(self.history_file):
            readline.read_history_file(self.history_file)
        self.cwd = os.getcwd()

    def write_history(self):
        readline.write_history_file(self.history_file)

    def do_quit(self, args):
        self.write_history()
        raise StopIteration

    def do_exit(self, args):
        self.do_quit(args)

    def do_EOF(self, args):
        print
        self.do_quit(args)

    def postcmd(self, line, bar):
        self.set_title()
        self.set_prompt()

    def set_prompt(self):
        if self.tree is not None:
            try:
                prompt_data = (self.tree.branch.nick, self.tree.branch.revno(),
                               self.tree.relpath('.'))
                prompt = " %s:%d/%s" % prompt_data
            except:
                prompt = ""
        else:
            prompt = ""
        self.prompt = "bzr%s> " % prompt

    def set_title(self, command=None):
        try:
            b = Branch.open_containing('.')[0]
            version = "%s:%d" % (b.nick, b.revno())
        except:
            version = "[no version]"
        if command is None:
            command = ""
        sys.stdout.write(terminal.term_title("bzr %s %s" % (command, version)))

    def do_cd(self, line):
        if line == "":
            line = "~"
        line = os.path.expanduser(line)
        if os.path.isabs(line):
            newcwd = line
        else:
            newcwd = self.cwd+'/'+line
        newcwd = os.path.normpath(newcwd)
        try:
            os.chdir(newcwd)
            self.cwd = newcwd
        except Exception, e:
            print e
        try:
            self.tree = WorkingTree.open_containing(".")[0]
        except:
            self.tree = None

    def do_help(self, line):
        self.default("help "+line)

    def default(self, line):
        args = shlex.split(line)
        alias_args = get_alias(args[0])
        if alias_args is not None:
            args[0] = alias_args.pop(0)

        commandname = args.pop(0)
        for char in ('|', '<', '>'):
            commandname = commandname.split(char)[0]
        if commandname[-1] in ('|', '<', '>'):
            commandname = commandname[:-1]
        try:
            if commandname in SHELL_BLACKLIST:
                raise BlackListedCommand(commandname)
            cmd_obj = get_cmd_object(commandname)
        except (BlackListedCommand, BzrError):
            return os.system(line)

        try:
            if too_complicated(line):
                return os.system("bzr "+line)
            else:
                return (cmd_obj.run_argv_aliases(args, alias_args) or 0)
        except BzrError, e:
            print e
        except KeyboardInterrupt, e:
            print "Interrupted"
        except Exception, e:
#            print "Unhandled error:\n%s" % errors.exception_str(e)
            print "Unhandled error:\n%s" % (e)


    def completenames(self, text, line, begidx, endidx):
        return CompletionContext(text).get_completions()

    def completedefault(self, text, line, begidx, endidx):
        """Perform completion for native commands.

        :param text: The text to complete
        :type text: str
        :param line: The entire line to complete
        :type line: str
        :param begidx: The start of the text in the line
        :type begidx: int
        :param endidx: The end of the text in the line
        :type endidx: int
        """
        (cmd, args, foo) = self.parseline(line)
        if cmd == "bzr":
            cmd = None
        return CompletionContext(text, command=cmd).get_completions()


def run_shell():
    try:
        prompt = PromptCmd()
        try:
            prompt.cmdloop()
        finally:
            prompt.write_history()
    except StopIteration:
        pass


def iter_opt_completions(command_obj):
    for option_name, option in command_obj.options().items():
        yield "--" + option_name
        short_name = option.short_name()
        if short_name:
            yield "-" + short_name


def iter_file_completions(arg, only_dirs = False):
    """Generate an iterator that iterates through filename completions.

    :param arg: The filename fragment to match
    :type arg: str
    :param only_dirs: If true, match only directories
    :type only_dirs: bool
    """
    cwd = os.getcwd()
    if cwd != "/":
        extras = [".", ".."]
    else:
        extras = []
    (dir, file) = os.path.split(arg)
    if dir != "":
        listingdir = os.path.expanduser(dir)
    else:
        listingdir = cwd
    for file in chain(os.listdir(listingdir), extras):
        if dir != "":
            userfile = dir+'/'+file
        else:
            userfile = file
        if userfile.startswith(arg):
            if os.path.isdir(listingdir+'/'+file):
                userfile+='/'
                yield userfile
            elif not only_dirs:
                yield userfile + ' '


def iter_dir_completions(arg):
    """Generate an iterator that iterates through directory name completions.

    :param arg: The directory name fragment to match
    :type arg: str
    """
    return iter_file_completions(arg, True)


def iter_command_names(hidden=False):
    for real_cmd_name, cmd_class in get_all_cmds():
        if not hidden and cmd_class.hidden:
            continue
        for name in [real_cmd_name] + cmd_class.aliases:
            # Don't complete on aliases that are prefixes of the canonical name
            if name == real_cmd_name or not real_cmd_name.startswith(name):
                yield name


def iter_executables(path):
    dirname, partial = os.path.split(path)
    for filename in os.listdir(dirname):
        if not filename.startswith(partial):
            continue
        fullpath = os.path.join(dirname, filename)
        mode=os.lstat(fullpath)[stat.ST_MODE]
        if stat.S_ISREG(mode) and 0111 & mode:
            yield fullpath + ' '


def filter_completions(iter, arg):
    return (c for c in iter if c.startswith(arg))


def iter_munged_completions(iter, arg, text):
    for completion in iter:
        completion = str(completion)
        if completion.startswith(arg):
            yield completion[len(arg)-len(text):]+" "


def too_complicated(line):
    for char in '|<>*?':
        if char in line:
            return True
    return False

    
### IPython mods start

def init_ipython(ip):
    def bzr_completer(self,ev):
        #print "bzr complete"
        tup =  ev.line.split(None,2)
        if len(tup) > 2:
            cmd = tup[1]
        else:
            cmd = None
                  
        return CompletionContext(ev.symbol, command = cmd).get_completions()
    bzrlib.plugin.load_plugins()
    ip.set_hook('complete_command', bzr_completer, str_key = 'bzr')    
