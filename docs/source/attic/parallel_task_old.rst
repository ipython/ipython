.. _paralleltask:

==========================
The IPython task interface
==========================

.. contents::

The ``Task`` interface to the controller presents the engines as a fault tolerant, dynamic load-balanced system or workers. Unlike the ``MultiEngine`` interface, in the ``Task`` interface, the user have no direct access to individual engines. In some ways, this interface is simpler, but in other ways it is more powerful. Best of all the user can use both of these interfaces at the same time to take advantage or both of their strengths.  When the user can break up the user's work into segments that do not depend on previous execution, the ``Task`` interface is ideal.  But it also has more power and flexibility, allowing the user to guide the distribution of jobs, without having to assign Tasks to engines explicitly.

Starting the IPython controller and engines
===========================================

To follow along with this tutorial, the user will need to start the IPython
controller and four IPython engines. The simplest way of doing this is to
use the ``ipcluster`` command::

	$ ipcluster -n 4
	
For more detailed information about starting the controller and engines, see our :ref:`introduction <parallel_overview>` to using IPython for parallel computing.

The magic here is that this single controller and set of engines is running both the MultiEngine and ``Task`` interfaces simultaneously.

QuickStart Task Farming
=======================

First, a quick example of how to start running the most basic Tasks.
The first step is to import the IPython ``client`` module and then create a ``TaskClient`` instance::
    
    In [1]: from IPython.kernel import client
    
    In [2]: tc = client.TaskClient()

Then the user wrap the commands the user want to run in Tasks::

    In [3]: tasklist = []
    In [4]: for n in range(1000):
        ...     tasklist.append(client.Task("a = %i"%n, pull="a"))

The first argument of the ``Task`` constructor is a string, the command to be executed.  The most important optional keyword argument is ``pull``, which can be a string or list of strings, and it specifies the variable names to be saved as results of the ``Task``.

Next, the user need to submit the Tasks to the ``TaskController`` with the ``TaskClient``::

    In [5]: taskids = [ tc.run(t) for t in tasklist ]

This will give the user a list of the TaskIDs used by the controller to keep track of the Tasks and their results.  Now at some point the user are going to want to get those results back.  The ``barrier`` method allows the user to wait for the Tasks to finish running::

    In [6]: tc.barrier(taskids)

This command will block until all the Tasks in ``taskids`` have finished.  Now, the user probably want to look at the user's results::

    In [7]: task_results = [ tc.get_task_result(taskid) for taskid in taskids ]

Now the user have a list of ``TaskResult`` objects, which have the actual result as a dictionary, but also keep track of some useful metadata about the ``Task``::

    In [8]: tr = ``Task``_results[73]
    
    In [9]: tr
    Out[9]: ``TaskResult``[ID:73]:{'a':73}
    
    In [10]: tr.engineid
    Out[10]: 1
    
    In [11]: tr.submitted, tr.completed, tr.duration
    Out[11]: ("2008/03/08 03:41:42", "2008/03/08 03:41:44", 2.12345)

The actual results are stored in a dictionary, ``tr.results``, and a namespace object ``tr.ns`` which accesses the result keys by attribute::

    In [12]: tr.results['a']
    Out[12]: 73
    
    In [13]: tr.ns.a
    Out[13]: 73

That should cover the basics of running simple Tasks.  There are several more powerful things the user can do with Tasks covered later.  The most useful probably being using a ``MutiEngineClient`` interface to initialize all the engines with the import dependencies necessary to run the user's Tasks.

There are many options for running and managing Tasks. The best way to learn further about the ``Task`` interface is to study the examples in ``docs/examples``. If the user do so and learn a lots about this interface, we encourage the user to expand this documentation about the ``Task`` system.

Overview of the Task System
===========================

The user's view of the ``Task`` system has three basic objects:  The ``TaskClient``, the ``Task``, and the ``TaskResult``.  The names of these three objects well indicate their role.

The ``TaskClient`` is the user's ``Task`` farming connection to the IPython cluster.  Unlike the ``MultiEngineClient``, the ``TaskControler`` handles all the scheduling and distribution of work, so the ``TaskClient`` has no notion of engines, it just submits Tasks and requests their results.  The Tasks are described as ``Task`` objects, and their results are wrapped in ``TaskResult`` objects.  Thus, there are very few necessary methods for the user to manage.

Inside the task system is a Scheduler object, which assigns tasks to workers.  The default scheduler is a simple FIFO queue.  Subclassing the Scheduler should be easy, just implementing your own priority system.

The TaskClient
==============

The ``TaskClient`` is the object the user use to connect to the ``Controller`` that is managing the user's Tasks.  It is the analog of the ``MultiEngineClient`` for the standard IPython multiplexing interface.  As with all client interfaces, the first step is to import the IPython Client Module::

    In [1]: from IPython.kernel import client

Just as with the ``MultiEngineClient``, the user create the ``TaskClient`` with a tuple, containing the ip-address and port of the ``Controller``.  the ``client`` module conveniently has the default address of the ``Task`` interface of the controller.  Creating a default ``TaskClient`` object would be done with this::

    In [2]: tc = client.TaskClient(client.default_task_address)

or, if the user want to specify a non default location of the ``Controller``, the user can specify explicitly::

    In [3]: tc = client.TaskClient(("192.168.1.1", 10113))

As discussed earlier, the ``TaskClient`` only has a few basic methods.

 * ``tc.run(task)``
    ``run`` is the method by which the user submits Tasks.  It takes exactly one argument, a ``Task`` object.  All the advanced control of ``Task`` behavior is handled by properties of the ``Task`` object, rather than the submission command, so they will be discussed later in the `Task`_ section.  ``run`` returns an integer, the ``Task``ID by which the ``Task`` and its results can be tracked and retrieved::
    
        In [4]: ``Task``ID = tc.run(``Task``)
    
 * ``tc.get_task_result(taskid, block=``False``)``
    ``get_task_result`` is the method by which results are retrieved.  It takes a single integer argument, the ``Task``ID`` of the result the user wish to retrieve.  ``get_task_result`` also takes a keyword argument ``block``.  ``block`` specifies whether the user actually want to wait for the result.  If ``block`` is false, as it is by default, ``get_task_result`` will return immediately.  If the ``Task`` has completed, it will return the ``TaskResult`` object for that ``Task``.  But if the ``Task`` has not completed, it will return ``None``.  If the user specify ``block=``True``, then ``get_task_result`` will wait for the ``Task`` to complete, and always return the ``TaskResult`` for the requested ``Task``.
 * ``tc.barrier(taskid(s))``
    ``barrier`` is a synchronization method.  It takes exactly one argument, a ``Task``ID or list of taskIDs.  ``barrier`` will block until all the specified Tasks have completed.  In practice, a barrier is often called between the ``Task`` submission section of the code and the result gathering section::
        
        In [5]: taskIDs = [ tc.run(``Task``) for ``Task`` in myTasks ]
        
        In [6]: tc.get_task_result(taskIDs[-1]) is None
        Out[6]: ``True``
        
        In [7]: tc.barrier(``Task``ID)
        
        In [8]: results = [ tc.get_task_result(tid) for tid in taskIDs ]
        
 * ``tc.queue_status(verbose=``False``)``
    ``queue_status`` is a method for querying the state of the ``TaskControler``.  ``queue_status`` returns a dict of the form::
        
        {'scheduled': Tasks that have been submitted but yet run
         'pending'  : Tasks that are currently running
         'succeeded': Tasks that have completed successfully
         'failed'   : Tasks that have finished with a failure
        }
    
    if @verbose is not specified (or is ``False``), then the values of the dict are integers - the number of Tasks in each state.  if @verbose is ``True``, then each element in the dict is a list of the taskIDs in that state::
    
        In [8]: tc.queue_status()
        Out[8]: {'scheduled': 4,
                'pending'  : 2,
                'succeeded': 5,
                'failed'   : 1
                }
        
        In [9]: tc.queue_status(verbose=True)
        Out[9]: {'scheduled': [8,9,10,11],
                'pending'  : [6,7],
                'succeeded': [0,1,2,4,5],
                'failed'   : [3]
                }
        
 * ``tc.abort(taskid)``
    ``abort`` allows the user to abort Tasks that have already been submitted.  ``abort`` will always return immediately.  If the ``Task`` has completed, ``abort`` will raise an ``IndexError ``Task`` Already Completed``.  An obvious case for ``abort`` would be where the user submits a long-running ``Task`` with a number of retries (see ``Task``_ section for how to specify retries) in an interactive session, but realizes there has been a typo.  The user can then abort the ``Task``, preventing certain failures from cluttering up the queue.  It can also be used for parallel search-type problems, where only one ``Task`` will give the solution, so once the user find the solution, the user would want to abort all remaining Tasks to prevent wasted work.
 * ``tc.spin()``
    ``spin`` simply triggers the scheduler in the ``TaskControler``.  Under most normal circumstances, this will do nothing.  The primary known usage case involves the ``Task`` dependency (see `Dependencies`_).  The dependency is a function of an Engine's ``properties``, but changing the ``properties`` via the ``MutliEngineClient`` does not trigger a reschedule event.  The main example case for this requires the following event sequence:
     * ``engine`` is available, ``Task`` is submitted, but ``engine`` does not have ``Task``'s dependencies.
     * ``engine`` gets necessary dependencies while no new Tasks are submitted or completed.
     * now ``engine`` can run ``Task``, but a ``Task`` event is required for the ``TaskControler`` to try scheduling ``Task`` again.
     
    ``spin`` is just an empty ping method to ensure that the Controller has scheduled all available Tasks, and should not be needed under most normal circumstances.

That covers the ``TaskClient``, a simple interface to the cluster.  With this, the user can submit jobs (and abort if necessary), request their results, synchronize on arbitrary subsets of jobs.

.. _task: The Task Object

The Task Object
===============

The ``Task`` is the basic object for describing a job.  It can be used in a very simple manner, where the user just specifies a command string to be executed as the ``Task``.  The usage of this first argument is exactly the same as the ``execute`` method of the ``MultiEngine`` (in fact, ``execute`` is called to run the code)::

    In [1]: t = client.Task("a = str(id)")
    
This ``Task`` would run, and store the string representation of the ``id`` element in ``a`` in each worker's namespace, but it is fairly useless because the user does not know anything about the state of the ``worker`` on which it ran at the time of retrieving results.  It is important that each ``Task`` not expect the state of the ``worker`` to persist after the ``Task`` is completed.  
There are many different situations for using ``Task`` Farming, and the ``Task`` object has many attributes for use in customizing the ``Task`` behavior.  All of a ``Task``'s attributes may be specified in the constructor, through keyword arguments, or after ``Task`` construction through attribute assignment.

Data Attributes
***************
It is likely that the user may want to move data around before or after executing the ``Task``.  We provide methods of sending data to initialize the worker's namespace, and specifying what data to bring back as the ``Task``'s results.

 * pull = []
    The obvious case is as above, where ``t`` would execute and store the result of ``myfunc`` in ``a``, it is likely that the user would want to bring ``a`` back to their namespace.  This is done through the ``pull`` attribute.  ``pull`` can be a string or list of strings, and it specifies the names of variables to be retrieved.  The ``TaskResult`` object retrieved by ``get_task_result`` will have a dictionary of keys and values, and the ``Task``'s ``pull`` attribute determines what goes into it::
        
        In [2]: t = client.Task("a = str(id)", pull = "a")
        
        In [3]: t = client.Task("a = str(id)", pull = ["a", "id"])
        
 * push = {}
    A user might also want to initialize some data into the namespace before the code part of the ``Task`` is run.  Enter ``push``.  ``push`` is a dictionary of key/value pairs to be loaded from the user's namespace into the worker's immediately before execution::

        In [4]: t = client.Task("a = f(submitted)", push=dict(submitted=time.time()), pull="a")

push and pull result directly in calling an ``engine``'s ``push`` and ``pull`` methods before and after ``Task`` execution respectively, and thus their api is the same.

Namespace Cleaning
******************
When a user is running a large number of Tasks, it is likely that the namespace of the worker's could become cluttered.  Some Tasks might be sensitive to clutter, while others might be known to cause namespace pollution.  For these reasons, Tasks have two boolean attributes for cleaning up the namespace.

 * ``clear_after``
    if clear_after is specified ``True``, the worker on which the ``Task`` was run will be reset (via ``engine.reset``) upon completion of the ``Task``.  This can be useful for both Tasks that produce clutter or Tasks whose intermediate data one might wish to be kept private::
    
        In [5]: t = client.Task("a = range(1e10)", pull = "a",clear_after=True)
        
    
 * ``clear_before``
    as one might guess, clear_before is identical to ``clear_after``, but it takes place before the ``Task`` is run.  This ensures that the ``Task`` runs on a fresh worker::

        In [6]: t = client.Task("a = globals()", pull = "a",clear_before=True)

Of course, a user can both at the same time, ensuring that all workers are clear except when they are currently running a job.  Both of these default to ``False``.

Fault Tolerance
***************
It is possible that Tasks might fail, and there are a variety of reasons this could happen.  One might be that the worker it was running on disconnected, and there was nothing wrong with the ``Task`` itself.  With the fault tolerance attributes of the ``Task``, the user can specify how many times to resubmit the ``Task``, and what to do if it never succeeds.

 * ``retries``
    ``retries`` is an integer, specifying the number of times a ``Task`` is to be retried.  It defaults to zero.  It is often a good idea for this number to be 1 or 2, to protect the ``Task`` from disconnecting engines, but not a large number.  If a ``Task`` is failing 100 times, there is probably something wrong with the ``Task``.  The canonical bad example:
    
        In [7]: t = client.Task("os.kill(os.getpid(), 9)", retries=99)
        
    This would actually take down 100 workers.
    
 * ``recovery_task``
    ``recovery_task`` is another ``Task`` object, to be run in the event of the original ``Task`` still failing after running out of retries.  Since ``recovery_task`` is another ``Task`` object, it can have its own ``recovery_task``.  The chain of Tasks is limitless, except loops are not allowed (that would be bad!).

Dependencies
************
Dependencies are the most powerful part of the ``Task`` farming system, because it allows the user to do some classification of the workers, and guide the ``Task`` distribution without meddling with the controller directly.  It makes use of two objects - the ``Task``'s ``depend`` attribute, and the engine's ``properties``.  See the `MultiEngine`_ reference for how to use engine properties.  The engine properties api exists for extending IPython, allowing conditional execution and new controllers that make decisions based on properties of its engines.  Currently the ``Task`` dependency is the only internal use of the properties api.

.. _MultiEngine: ./parallel_multiengine

The ``depend`` attribute of a ``Task`` must be a function of exactly one argument, the worker's properties dictionary, and it should return ``True`` if the ``Task`` should be allowed to run on the worker and ``False`` if not.  The usage in the controller is fault tolerant, so exceptions raised by ``Task.depend`` will be ignored and functionally equivalent to always returning ``False``.  Tasks`` with invalid ``depend`` functions will never be assigned to a worker::

    In [8]: def dep(properties):
        ...     return properties["RAM"] > 2**32 # have at least 4GB
    In [9]: t = client.Task("a = bigfunc()", depend=dep)
    
It is important to note that assignment of values to the properties dict is done entirely by the user, either locally (in the engine) using the EngineAPI, or remotely, through the ``MultiEngineClient``'s get/set_properties methods.





    
