""" Preliminary "job control" extensions for IPython

requires python 2.4 (or separate 'subprocess' module

This provides 2 features, launching background jobs and killing foreground jobs from another IPython instance.

Launching background jobs:

    Usage:

    [ipython]|2> import jobctrl
    [ipython]|3> &ls
             <3> <jobctrl.IpyPopen object at 0x00D87FD0>
    [ipython]|4> _3.go
    -----------> _3.go()
    ChangeLog
    IPython
    MANIFEST.in
    README
    README_Windows.txt

    ...

Killing foreground tasks:

Launch IPython instance, run a blocking command:

    [Q:/ipython]|1> import jobctrl
    [Q:/ipython]|2> cat

Now launch a new IPython prompt and kill the process:

    IPython 0.8.3.svn.r2919   [on Py 2.5]
    [Q:/ipython]|1> import jobctrl
    [Q:/ipython]|2> %tasks
    6020: 'cat ' (Q:\ipython)
    [Q:/ipython]|3> %kill
    SUCCESS: The process with PID 6020 has been terminated.
    [Q:/ipython]|4>

(you don't need to specify PID for %kill if only one task is running)
"""

from subprocess import *
import os,shlex,sys,time
import threading,Queue

from IPython.core import ipapi
from IPython.core.error import TryNext
from IPython.utils.text import make_quoted_expr

if os.name == 'nt':
    def kill_process(pid):
        os.system('taskkill /F /PID %d' % pid)
else:
    def kill_process(pid):
        os.system('kill -9 %d' % pid)



class IpyPopen(Popen):
    def go(self):
        print self.communicate()[0]
    def __repr__(self):
        return '<IPython job "%s" PID=%d>' % (self.line, self.pid)

    def kill(self):
        kill_process(self.pid)

def startjob(job):
    p = IpyPopen(shlex.split(job), stdout=PIPE, shell = False)
    p.line = job
    return p

class AsyncJobQ(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q = Queue.Queue()
        self.output = []
        self.stop = False
    def run(self):
        while 1:
            cmd,cwd = self.q.get()
            if self.stop:
                self.output.append("** Discarding: '%s' - %s" % (cmd,cwd))
                continue
            self.output.append("** Task started: '%s' - %s" % (cmd,cwd))

            p = Popen(cmd, shell=True, stdout=PIPE, stderr=STDOUT, cwd = cwd)
            out = p.stdout.read()
            self.output.append("** Task complete: '%s'\n" % cmd)
            self.output.append(out)

    def add(self,cmd):
        self.q.put_nowait((cmd, os.getcwdu()))

    def dumpoutput(self):
        while self.output:
            item = self.output.pop(0)
            print item

_jobq = None

def jobqueue_f(self, line):

    global _jobq
    if not _jobq:
        print "Starting jobqueue - do '&some_long_lasting_system_command' to enqueue"
        _jobq = AsyncJobQ()
        _jobq.setDaemon(True)
        _jobq.start()
        ip.jobq = _jobq.add
        return
    if line.strip() == 'stop':
        print "Stopping and clearing jobqueue, %jobqueue start to start again"
        _jobq.stop = True
        return
    if line.strip() == 'start':
        _jobq.stop = False
        return

def jobctrl_prefilter_f(self,line):
    if line.startswith('&'):
        pre,fn,rest = self.split_user_input(line[1:])

        line = ip.expand_aliases(fn,rest)
        if not _jobq:
            return 'get_ipython().startjob(%s)' % make_quoted_expr(line)
        return 'get_ipython().jobq(%s)' % make_quoted_expr(line)

    raise TryNext

def jobq_output_hook(self):
    if not _jobq:
        return
    _jobq.dumpoutput()



def job_list(ip):
    keys = ip.db.keys('tasks/*')
    ents = [ip.db[k] for k in keys]
    return ents

def magic_tasks(self,line):
    """ Show a list of tasks.

    A 'task' is a process that has been started in IPython when 'jobctrl' extension is enabled.
    Tasks can be killed with %kill.

    '%tasks clear' clears the task list (from stale tasks)
    """
    ip = self.getapi()
    if line.strip() == 'clear':
        for k in ip.db.keys('tasks/*'):
            print "Clearing",ip.db[k]
            del ip.db[k]
        return

    ents = job_list(ip)
    if not ents:
        print "No tasks running"
    for pid,cmd,cwd,t in ents:
        dur = int(time.time()-t)
        print "%d: '%s' (%s) %d:%02d" % (pid,cmd,cwd, dur / 60,dur%60)

def magic_kill(self,line):
    """ Kill a task

    Without args, either kill one task (if only one running) or show list (if many)
    With arg, assume it's the process id.

    %kill is typically (much) more powerful than trying to terminate a process with ctrl+C.
    """
    ip = self.getapi()
    jobs  = job_list(ip)

    if not line.strip():
        if len(jobs) == 1:
            kill_process(jobs[0][0])
        else:
            magic_tasks(self,line)
        return

    try:
        pid = int(line)
        kill_process(pid)
    except ValueError:
        magic_tasks(self,line)

if sys.platform == 'win32':
    shell_internal_commands = 'break chcp cls copy ctty date del erase dir md mkdir path prompt rd rmdir start time type ver vol'.split()
    PopenExc = WindowsError
else:
    # todo linux commands
    shell_internal_commands = []
    PopenExc = OSError


def jobctrl_shellcmd(ip,cmd):
    """ os.system replacement that stores process info to db['tasks/t1234'] """
    cmd = cmd.strip()
    cmdname = cmd.split(None,1)[0]
    if cmdname in shell_internal_commands or '|' in cmd or '>' in cmd or '<' in cmd:
        use_shell = True
    else:
        use_shell = False

    jobentry = None
    try:
        try:
            p = Popen(cmd,shell = use_shell)
        except PopenExc :
            if use_shell:
                # try with os.system
                os.system(cmd)
                return
            else:
                # have to go via shell, sucks
                p = Popen(cmd,shell = True)

        jobentry = 'tasks/t' + str(p.pid)
        ip.db[jobentry] = (p.pid,cmd,os.getcwdu(),time.time())
        p.communicate()

    finally:
        if jobentry:
            del ip.db[jobentry]


def install():
    global ip
    ip = ipapi.get()
    # needed to make startjob visible as _ip.startjob('blah')
    ip.startjob = startjob
    ip.set_hook('input_prefilter', jobctrl_prefilter_f)
    ip.set_hook('shell_hook', jobctrl_shellcmd)
    ip.define_magic('kill',magic_kill)
    ip.define_magic('tasks',magic_tasks)
    ip.define_magic('jobqueue',jobqueue_f)
    ip.set_hook('pre_prompt_hook', jobq_output_hook)
install()
