# -*- coding: utf-8 -*-
"""Manage background (threaded) jobs conveniently from an interactive shell.

This module provides a BackgroundJobManager class.  This is the main class
meant for public usage, it implements an object which can create and manage
new background jobs.

It also provides the actual job classes managed by these BackgroundJobManager
objects, see their docstrings below.


This system was inspired by discussions with B. Granger and the
BackgroundCommand class described in the book Python Scripting for
Computational Science, by H. P. Langtangen:

http://folk.uio.no/hpl/scripting

(although ultimately no code from this text was used, as IPython's system is a
separate implementation).

$Id: background_jobs.py 994 2006-01-08 08:29:44Z fperez $
"""

#*****************************************************************************
#       Copyright (C) 2005-2006 Fernando Perez <fperez@colorado.edu>
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

from IPython import Release
__author__  = '%s <%s>' % Release.authors['Fernando']
__license__ = Release.license

# Code begins
import sys
import threading

from IPython.ultraTB import AutoFormattedTB
from IPython.genutils import warn,error

class BackgroundJobManager:
    """Class to manage a pool of backgrounded threaded jobs.

    Below, we assume that 'jobs' is a BackgroundJobManager instance.
    
    Usage summary (see the method docstrings for details):

      jobs.new(...) -> start a new job
      
      jobs() or jobs.status() -> print status summary of all jobs

      jobs[N] -> returns job number N.

      foo = jobs[N].result -> assign to variable foo the result of job N

      jobs[N].traceback() -> print the traceback of dead job N

      jobs.remove(N) -> remove (finished) job N

      jobs.flush_finished() -> remove all finished jobs
      
    As a convenience feature, BackgroundJobManager instances provide the
    utility result and traceback methods which retrieve the corresponding
    information from the jobs list:

      jobs.result(N) <--> jobs[N].result
      jobs.traceback(N) <--> jobs[N].traceback()

    While this appears minor, it allows you to use tab completion
    interactively on the job manager instance.

    In interactive mode, IPython provides the magic fuction %bg for quick
    creation of backgrounded expression-based jobs. Type bg? for details."""

    def __init__(self):
        # Lists for job management
        self.jobs_run  = []
        self.jobs_comp = []
        self.jobs_dead = []
        # A dict of all jobs, so users can easily access any of them
        self.jobs_all = {}
        # For reporting
        self._comp_report = []
        self._dead_report = []
        # Store status codes locally for fast lookups
        self._s_created   = BackgroundJobBase.stat_created_c
        self._s_running   = BackgroundJobBase.stat_running_c
        self._s_completed = BackgroundJobBase.stat_completed_c
        self._s_dead      = BackgroundJobBase.stat_dead_c

    def new(self,func_or_exp,*args,**kwargs):
        """Add a new background job and start it in a separate thread.

        There are two types of jobs which can be created:

        1. Jobs based on expressions which can be passed to an eval() call.
        The expression must be given as a string.  For example:

          job_manager.new('myfunc(x,y,z=1)'[,glob[,loc]])

        The given expression is passed to eval(), along with the optional
        global/local dicts provided.  If no dicts are given, they are
        extracted automatically from the caller's frame.
        
        A Python statement is NOT a valid eval() expression.  Basically, you
        can only use as an eval() argument something which can go on the right
        of an '=' sign and be assigned to a variable.

        For example,"print 'hello'" is not valid, but '2+3' is.

        2. Jobs given a function object, optionally passing additional
        positional arguments:

          job_manager.new(myfunc,x,y)

        The function is called with the given arguments.

        If you need to pass keyword arguments to your function, you must
        supply them as a dict named kw:

          job_manager.new(myfunc,x,y,kw=dict(z=1))

        The reason for this assymmetry is that the new() method needs to
        maintain access to its own keywords, and this prevents name collisions
        between arguments to new() and arguments to your own functions.

        In both cases, the result is stored in the job.result field of the
        background job object.


        Notes and caveats:

        1. All threads running share the same standard output.  Thus, if your
        background jobs generate output, it will come out on top of whatever
        you are currently writing.  For this reason, background jobs are best
        used with silent functions which simply return their output.

        2. Threads also all work within the same global namespace, and this
        system does not lock interactive variables.  So if you send job to the
        background which operates on a mutable object for a long time, and
        start modifying that same mutable object interactively (or in another
        backgrounded job), all sorts of bizarre behaviour will occur.

        3. If a background job is spending a lot of time inside a C extension
        module which does not release the Python Global Interpreter Lock
        (GIL), this will block the IPython prompt.  This is simply because the
        Python interpreter can only switch between threads at Python
        bytecodes.  While the execution is inside C code, the interpreter must
        simply wait unless the extension module releases the GIL.

        4. There is no way, due to limitations in the Python threads library,
        to kill a thread once it has started."""
        
        if callable(func_or_exp):
            kw  = kwargs.get('kw',{})
            job = BackgroundJobFunc(func_or_exp,*args,**kw)
        elif isinstance(func_or_exp,basestring):
            if not args:
                frame = sys._getframe(1)
                glob, loc = frame.f_globals, frame.f_locals
            elif len(args)==1:
                glob = loc = args[0]
            elif len(args)==2:
                glob,loc = args
            else:
                raise ValueError,\
                      'Expression jobs take at most 2 args (globals,locals)'
            job = BackgroundJobExpr(func_or_exp,glob,loc)
        else:
            raise
        jkeys = self.jobs_all.keys()
        if jkeys:
            job.num = max(jkeys)+1
        else:
            job.num = 0
        self.jobs_run.append(job)
        self.jobs_all[job.num] = job
        print 'Starting job # %s in a separate thread.' % job.num
        job.start()
        return job

    def __getitem__(self,key):
        return self.jobs_all[key]

    def __call__(self):
        """An alias to self.status(),

        This allows you to simply call a job manager instance much like the
        Unix jobs shell command."""

        return self.status()

    def _update_status(self):
        """Update the status of the job lists.

        This method moves finished jobs to one of two lists:
          - self.jobs_comp: jobs which completed successfully
          - self.jobs_dead: jobs which finished but died.

        It also copies those jobs to corresponding _report lists.  These lists
        are used to report jobs completed/dead since the last update, and are
        then cleared by the reporting function after each call."""
        
        run,comp,dead = self._s_running,self._s_completed,self._s_dead
        jobs_run = self.jobs_run
        for num in range(len(jobs_run)):
            job  = jobs_run[num]
            stat = job.stat_code
            if stat == run:
                continue
            elif stat == comp:
                self.jobs_comp.append(job)
                self._comp_report.append(job)
                jobs_run[num] = False
            elif stat == dead:
                self.jobs_dead.append(job)
                self._dead_report.append(job)
                jobs_run[num] = False
        self.jobs_run = filter(None,self.jobs_run)

    def _group_report(self,group,name):
        """Report summary for a given job group.

        Return True if the group had any elements."""

        if group:
            print '%s jobs:' % name
            for job in group:
                print '%s : %s' % (job.num,job)
            print
            return True

    def _group_flush(self,group,name):
        """Flush a given job group

        Return True if the group had any elements."""

        njobs = len(group)
        if njobs:
            plural = {1:''}.setdefault(njobs,'s')
            print 'Flushing %s %s job%s.' % (njobs,name,plural)
            group[:] = []
            return True
        
    def _status_new(self):
        """Print the status of newly finished jobs.

        Return True if any new jobs are reported.

        This call resets its own state every time, so it only reports jobs
        which have finished since the last time it was called."""

        self._update_status()
        new_comp = self._group_report(self._comp_report,'Completed')
        new_dead = self._group_report(self._dead_report,
                                      'Dead, call job.traceback() for details')
        self._comp_report[:] = []
        self._dead_report[:] = []
        return new_comp or new_dead
                
    def status(self,verbose=0):
        """Print a status of all jobs currently being managed."""

        self._update_status()
        self._group_report(self.jobs_run,'Running')
        self._group_report(self.jobs_comp,'Completed')
        self._group_report(self.jobs_dead,'Dead')
        # Also flush the report queues
        self._comp_report[:] = []
        self._dead_report[:] = []

    def remove(self,num):
        """Remove a finished (completed or dead) job."""

        try:
            job = self.jobs_all[num]
        except KeyError:
            error('Job #%s not found' % num)
        else:
            stat_code = job.stat_code
            if stat_code == self._s_running:
                error('Job #%s is still running, it can not be removed.' % num)
                return
            elif stat_code == self._s_completed:
                self.jobs_comp.remove(job)
            elif stat_code == self._s_dead:
                self.jobs_dead.remove(job)

    def flush_finished(self):
        """Flush all jobs finished (completed and dead) from lists.

        Running jobs are never flushed.

        It first calls _status_new(), to update info. If any jobs have
        completed since the last _status_new() call, the flush operation
        aborts."""

        if self._status_new():
            error('New jobs completed since last '\
                  '_status_new(), aborting flush.')
            return

        # Remove the finished jobs from the master dict
        jobs_all = self.jobs_all
        for job in self.jobs_comp+self.jobs_dead:
            del(jobs_all[job.num])

        # Now flush these lists completely
        fl_comp = self._group_flush(self.jobs_comp,'Completed')
        fl_dead = self._group_flush(self.jobs_dead,'Dead')
        if not (fl_comp or fl_dead):
            print 'No jobs to flush.'

    def result(self,num):
        """result(N) -> return the result of job N."""
        try:
            return self.jobs_all[num].result
        except KeyError:
            error('Job #%s not found' % num)

    def traceback(self,num):
        try:
            self.jobs_all[num].traceback()
        except KeyError:
            error('Job #%s not found' % num)


class BackgroundJobBase(threading.Thread):
    """Base class to build BackgroundJob classes.

    The derived classes must implement:

    - Their own __init__, since the one here raises NotImplementedError.  The
    derived constructor must call self._init() at the end, to provide common
    initialization.

    - A strform attribute used in calls to __str__.

    - A call() method, which will make the actual execution call and must
    return a value to be held in the 'result' field of the job object."""

    # Class constants for status, in string and as numerical codes (when
    # updating jobs lists, we don't want to do string comparisons).  This will
    # be done at every user prompt, so it has to be as fast as possible
    stat_created   = 'Created'; stat_created_c = 0
    stat_running   = 'Running'; stat_running_c = 1
    stat_completed = 'Completed'; stat_completed_c = 2
    stat_dead      = 'Dead (Exception), call job.traceback() for details'
    stat_dead_c = -1

    def __init__(self):
        raise NotImplementedError, \
              "This class can not be instantiated directly."

    def _init(self):
        """Common initialization for all BackgroundJob objects"""
        
        for attr in ['call','strform']:
            assert hasattr(self,attr), "Missing attribute <%s>" % attr
        
        # The num tag can be set by an external job manager
        self.num = None
      
        self.status    = BackgroundJobBase.stat_created
        self.stat_code = BackgroundJobBase.stat_created_c
        self.finished  = False
        self.result    = '<BackgroundJob has not completed>'
        # reuse the ipython traceback handler if we can get to it, otherwise
        # make a new one
        try:
            self._make_tb = __IPYTHON__.InteractiveTB.text
        except:
            self._make_tb = AutoFormattedTB(mode = 'Context',
                                           color_scheme='NoColor',
                                           tb_offset = 1).text
        # Hold a formatted traceback if one is generated.
        self._tb = None
        
        threading.Thread.__init__(self)

    def __str__(self):
        return self.strform

    def __repr__(self):
        return '<BackgroundJob: %s>' % self.strform

    def traceback(self):
        print self._tb
        
    def run(self):
        try:
            self.status    = BackgroundJobBase.stat_running
            self.stat_code = BackgroundJobBase.stat_running_c
            self.result    = self.call()
        except:
            self.status    = BackgroundJobBase.stat_dead
            self.stat_code = BackgroundJobBase.stat_dead_c
            self.finished  = None
            self.result    = ('<BackgroundJob died, call job.traceback() for details>')
            self._tb       = self._make_tb()
        else:
            self.status    = BackgroundJobBase.stat_completed
            self.stat_code = BackgroundJobBase.stat_completed_c
            self.finished  = True

class BackgroundJobExpr(BackgroundJobBase):
    """Evaluate an expression as a background job (uses a separate thread)."""

    def __init__(self,expression,glob=None,loc=None):
        """Create a new job from a string which can be fed to eval().

        global/locals dicts can be provided, which will be passed to the eval
        call."""

        # fail immediately if the given expression can't be compiled
        self.code = compile(expression,'<BackgroundJob compilation>','eval')
                
        if glob is None:
            glob = {}
        if loc is None:
            loc = {}
            
        self.expression = self.strform = expression
        self.glob = glob
        self.loc = loc
        self._init()
        
    def call(self):
        return eval(self.code,self.glob,self.loc)

class BackgroundJobFunc(BackgroundJobBase):
    """Run a function call as a background job (uses a separate thread)."""

    def __init__(self,func,*args,**kwargs):
        """Create a new job from a callable object.

        Any positional arguments and keyword args given to this constructor
        after the initial callable are passed directly to it."""

        assert callable(func),'first argument must be callable'
        
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        
        self.func = func
        self.args = args
        self.kwargs = kwargs
        # The string form will only include the function passed, because
        # generating string representations of the arguments is a potentially
        # _very_ expensive operation (e.g. with large arrays).
        self.strform = str(func)
        self._init()

    def call(self):
        return self.func(*self.args,**self.kwargs)


if __name__=='__main__':

    import time

    def sleepfunc(interval=2,*a,**kw):
        args = dict(interval=interval,
                    args=a,
                    kwargs=kw)
        time.sleep(interval)
        return args

    def diefunc(interval=2,*a,**kw):
        time.sleep(interval)
        die

    def printfunc(interval=1,reps=5):
        for n in range(reps):
            time.sleep(interval)
            print 'In the background...'

    jobs = BackgroundJobManager()
    # first job will have # 0
    jobs.new(sleepfunc,4)
    jobs.new(sleepfunc,kw={'reps':2})
    # This makes a job which will die
    jobs.new(diefunc,1)
    jobs.new('printfunc(1,3)')

    # after a while, you can get the traceback of a dead job.  Run the line
    # below again interactively until it prints a traceback (check the status
    # of the job):
    print jobs[1].status
    jobs[1].traceback()
    
    # Run this line again until the printed result changes
    print "The result of job #0 is:",jobs[0].result
