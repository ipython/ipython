""" Tab completion support for a couple of linux package managers 

This is also an example of how to write custom completer plugins
or hooks.

Practical use:

[ipython]|1> import ipy_linux_package_managers
[ipython]|2> apt-get u<<< press tab here >>>
update  upgrade
[ipython]|2> apt-get up

"""
import IPython.ipapi

ip = IPython.ipapi.get()

def apt_completers(self, event):
    """ This should return a list of strings with possible completions.
    
    Note that all the included strings that don't start with event.symbol
    are removed, in order to not confuse readline.
    
    """
    # print event # dbg
    
    # commands are only suggested for the 'command' part of package manager
    # invocation
        
    cmd = (event.line + "<placeholder>").rsplit(None,1)[0]
    # print cmd
    if cmd.endswith('apt-get') or cmd.endswith('yum'):
        return ['update', 'upgrade', 'install', 'remove']
    
    # later on, add dpkg -l / whatever to get list of possible 
    # packages, add switches etc. for the rest of command line
    # filling
    
    raise IPython.ipapi.TryNext 


# re_key specifies the regexp that triggers the specified completer

ip.set_hook('complete_command', apt_completers, re_key = '.*apt-get')
ip.set_hook('complete_command', apt_completers, re_key = '.*yum')

py_std_modules = """\
BaseHTTPServer Bastion CGIHTTPServer ConfigParser Cookie
DocXMLRPCServer HTMLParser MimeWriter Queue SimpleHTTPServer
SimpleXMLRPCServer SocketServer StringIO UserDict UserList UserString
_LWPCookieJar _MozillaCookieJar __future__ __phello__.foo _strptime
_threading_local aifc anydbm asynchat asyncore atexit audiodev base64
bdb binhex bisect cProfile calendar cgi cgitb chunk cmd code codecs
codeop colorsys commands compileall contextlib cookielib copy copy_reg
csv dbhash decimal difflib dircache dis doctest dumbdbm dummy_thread
dummy_threading filecmp fileinput fnmatch formatter fpformat ftplib
functools getopt getpass gettext glob gopherlib gzip hashlib heapq
hmac htmlentitydefs htmllib httplib ihooks imaplib imghdr imputil
inspect keyword linecache locale macpath macurl2path mailbox mailcap
markupbase md5 mhlib mimetools mimetypes mimify modulefinder multifile
mutex netrc new nntplib ntpath nturl2path opcode optparse os
os2emxpath pdb pickle pickletools pipes pkgutil platform popen2 poplib
posixfile posixpath pprint profile pstats pty py_compile pyclbr pydoc
quopri random re repr rexec rfc822 rlcompleter robotparser runpy sched
sets sgmllib sha shelve shlex shutil site smtpd smtplib sndhdr socket
sre sre_compile sre_constants sre_parse stat statvfs string stringold
stringprep struct subprocess sunau sunaudio symbol symtable tabnanny
tarfile telnetlib tempfile textwrap this threading timeit toaiff token
tokenize trace traceback tty types unittest urllib urllib2 urlparse
user uu uuid warnings wave weakref webbrowser whichdb xdrlib xmllib
xmlrpclib zipfile"""

def module_completer(self,event):    
    """ Give completions after user has typed 'import' """
    return py_std_modules.split()

ip.set_hook('complete_command', module_completer, str_key = 'import')

svn_commands = """\
add blame praise annotate ann cat checkout co cleanup commit ci copy
cp delete del remove rm diff di export help ? h import info list ls
lock log merge mkdir move mv rename ren propdel pdel pd propedit pedit
pe propget pget pg proplist plist pl propset pset ps resolved revert
status stat st switch sw unlock
"""

def svn_completer(self,even):
    return svn_commands.split()

ip.set_hook('complete_command', svn_completer, str_key = 'svn')