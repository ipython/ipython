# Online Python Tutor
# https://github.com/pgbovine/OnlinePythonTutor/
#
# Copyright (C) 2010-2012 Philip J. Guo (philip@pgbovine.net)
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


# This is the meat of the Online Python Tutor back-end.  It implements a
# full logger for Python program execution (based on pdb, the standard
# Python debugger imported via the bdb module), printing out the values
# of all in-scope data structures after each executed instruction.



import sys
import bdb # the KEY import here!
import re
import traceback
import types

is_python3 = (sys.version_info[0] == 3)

if is_python3:
  import io as cStringIO
else:
  import cStringIO
import pg_encoder


# TODO: not threadsafe:

# upper-bound on the number of executed lines, in order to guard against
# infinite loops
MAX_EXECUTED_LINES = 300

#DEBUG = False
DEBUG = True


# simple sandboxing scheme:
#
# - use resource.setrlimit to deprive this process of ANY file descriptors
#   (which will cause file read/write and subprocess shell launches to fail)
# - restrict user builtins and module imports
#   (beware that this is NOT foolproof at all ... there are known flaws!)
#
# ALWAYS use defense-in-depth and don't just rely on these simple mechanisms
# try:
#   import resource
#   resource_module_loaded = True
# except ImportError:
#   # Google App Engine doesn't seem to have the 'resource' module
#   resource_module_loaded = False


# ugh, I can't figure out why in Python 2, __builtins__ seems to
# be a dict, but in Python 3, __builtins__ seems to be a module,
# so just handle both cases ... UGLY!
if type(__builtins__) is dict:
  BUILTIN_IMPORT = __builtins__['__import__']
else:
  assert type(__builtins__) is types.ModuleType
  BUILTIN_IMPORT = __builtins__.__import__


# whitelist of module imports
# ALLOWED_MODULE_IMPORTS = ('math', 'random', 'datetime',
#                           'functools', 'operator', 'string',
#                           'collections', 're', 'json',
#                           'heapq', 'bisect')

# PREEMPTIVELY import all of these modules, so that when the user's
# script imports them, it won't try to do a file read (since they've
# already been imported and cached in memory). Remember that when
# the user's code runs, resource.setrlimit(resource.RLIMIT_NOFILE, (0, 0))
# will already be in effect, so no more files can be opened.
# for m in ALLOWED_MODULE_IMPORTS:
#   __import__(m)


# Restrict imports to a whitelist
# def __restricted_import__(*args):
#   if args[0] in ALLOWED_MODULE_IMPORTS:
#     return BUILTIN_IMPORT(*args)
#   else:
#     raise ImportError('{0} not supported'.format(args[0]))


# blacklist of builtins
BANNED_BUILTINS = ()


IGNORE_VARS = set((
    '__builtins__', '__name__', '__exception__', '__doc__', '__package__',
    '_dh', '_', '__', '___', 'quit', 'exit', 'get_ipython', '_sh', '_dh', '_oh', 'In', 'Out'
))

def get_user_stdout(frame):
  return frame.f_globals['__user_stdout__'].getvalue()

def get_user_globals(frame):
  d = filter_var_dict(frame.f_globals)
  # also filter out __return__ for globals only, but NOT for locals
  if '__return__' in d:
    del d['__return__']
  return d

def get_user_locals(frame):
  return filter_var_dict(frame.f_locals)

def filter_var_dict(d):
  ret = {}
  for (k,v) in d.items():
    if k not in IGNORE_VARS:
      ret[k] = v
  return ret


# yield all function objects locally-reachable from frame,
# making sure to traverse inside all compound objects ...
def visit_all_locally_reachable_function_objs(frame):
  for (k, v) in get_user_locals(frame).items():
    for e in visit_function_obj(v, set()):
      if e: # only non-null if it's a function object
        assert type(e) in (types.FunctionType, types.MethodType)
        yield e


# TODO: this might be slow if we're traversing inside lots of objects:
def visit_function_obj(v, ids_seen_set):
  v_id = id(v)

  # to prevent infinite loop
  if v_id in ids_seen_set:
    yield None
  else:
    ids_seen_set.add(v_id)

    typ = type(v)
    
    # simple base case
    if typ in (types.FunctionType, types.MethodType):
      yield v

    # recursive cases
    elif typ in (list, tuple, set):
      for child in v:
        for child_res in visit_function_obj(child, ids_seen_set):
          yield child_res

    elif typ == dict or pg_encoder.is_class(v) or pg_encoder.is_instance(v):
      contents_dict = None

      if typ == dict:
        contents_dict = v
      # warning: some classes or instances don't have __dict__ attributes
      elif hasattr(v, '__dict__'):
        contents_dict = v.__dict__

      if contents_dict:
        for (key_child, val_child) in contents_dict.items():
          for key_child_res in visit_function_obj(key_child, ids_seen_set):
            yield key_child_res
          for val_child_res in visit_function_obj(val_child, ids_seen_set):
            yield val_child_res

    # degenerate base case
    yield None


class PGLogger(bdb.Bdb):

    def __init__(self, cumulative_mode, finalizer_func):
        bdb.Bdb.__init__(self)
        self.mainpyfile = ''
        self._wait_for_mainpyfile = 0

        # a function that takes the output trace as a parameter and
        # processes it
        self.finalizer_func = finalizer_func

        # if True, then displays ALL stack frames that have ever existed
        # rather than only those currently on the stack (and their
        # lexical parents)
        self.cumulative_mode = cumulative_mode

        # each entry contains a dict with the information for a single
        # executed line
        self.trace = []

        #http://stackoverflow.com/questions/2112396/in-python-in-google-app-engine-how-do-you-capture-output-produced-by-the-print
        self.GAE_STDOUT = sys.stdout

        # Key:   function object
        # Value: parent frame
        self.closures = {}

        # set of function objects that were defined in the global scope
        self.globally_defined_funcs = set()

        # Key: frame object
        # Value: monotonically increasing small ID, based on call order
        self.frame_ordered_ids = {}
        self.cur_frame_id = 1

        # List of frames to KEEP AROUND after the function exits.
        # If cumulative_mode is True, then keep ALL frames in
        # zombie_frames; otherwise keep only frames where
        # nested functions were defined within them.
        self.zombie_frames = []

        # set of elements within zombie_frames that are also
        # LEXICAL PARENTS of other frames
        self.parent_frames_set = set()

        # all globals that ever appeared in the program, in the order in
        # which they appeared. note that this might be a superset of all
        # the globals that exist at any particular execution point,
        # since globals might have been deleted (using, say, 'del')
        self.all_globals_in_order = []

        # very important for this single object to persist throughout
        # execution, or else canonical small IDs won't be consistent.
        self.encoder = pg_encoder.ObjectEncoder()

        self.executed_script = None # Python script to be executed!


    def get_frame_id(self, cur_frame):
      return self.frame_ordered_ids[cur_frame]

    # Returns the (lexical) parent of a function value.
    def get_parent_of_function(self, val):
      if val not in self.closures:
        return None
      return self.get_frame_id(self.closures[val])


    # Returns the (lexical) parent frame of the function that was called
    # to create the stack frame 'frame'.
    #
    # OKAY, this is a SUPER hack, but I don't see a way around it
    # since it's impossible to tell exactly which function
    # ('closure') object was called to create 'frame'.
    #
    # The Python interpreter doesn't maintain this information,
    # so unless we hack the interpreter, we will simply have
    # to make an educated guess based on the contents of local
    # variables inherited from possible parent frame candidates.
    def get_parent_frame(self, frame):
      for (func_obj, parent_frame) in self.closures.items():
        # ok, there's a possible match, but let's compare the
        # local variables in parent_frame to those of frame
        # to make sure. this is a hack that happens to work because in
        # Python, each stack frame inherits ('inlines') a copy of the
        # variables from its (lexical) parent frame.
        if func_obj.__code__ == frame.f_code:
          all_matched = True
          for k in frame.f_locals:
            # Do not try to match local names
            if k in frame.f_code.co_varnames:
              continue
            if k != '__return__' and k in parent_frame.f_locals:
              if parent_frame.f_locals[k] != frame.f_locals[k]:
                all_matched = False
                break

          if all_matched:
            return parent_frame

      return None


    def lookup_zombie_frame_by_id(self, frame_id):
      # TODO: kinda inefficient
      for e in self.zombie_frames:
        if self.get_frame_id(e) == frame_id:
          return e
      assert False # should never get here


    # unused ...
    #def reset(self):
    #    bdb.Bdb.reset(self)
    #    self.forget()


    def forget(self):
        self.lineno = None
        self.stack = []
        self.curindex = 0
        self.curframe = None

    def setup(self, f, t):
        self.forget()
        self.stack, self.curindex = self.get_stack(f, t)
        self.curframe = self.stack[self.curindex][0]


    # Override Bdb methods

    def user_call(self, frame, argument_list):
        """This method is called when there is the remote possibility
        that we ever need to stop in this function."""
        if self._wait_for_mainpyfile:
            return
        if self.stop_here(frame):
            # delete __return__ so that on subsequent calls to
            # a generator function, the OLD yielded (returned)
            # value gets deleted from the frame ...
            try:
              del frame.f_locals['__return__']
            except KeyError:
              pass

            self.interaction(frame, None, 'call')

    def user_line(self, frame):
        """This function is called when we stop or break at this line."""
        if self._wait_for_mainpyfile:
            if (self.canonic(frame.f_code.co_filename) != "<string>" or
                frame.f_lineno <= 0):
                return
            self._wait_for_mainpyfile = 0
        self.interaction(frame, None, 'step_line')

    def user_return(self, frame, return_value):
        """This function is called when a return trap is set here."""
        frame.f_locals['__return__'] = return_value
        self.interaction(frame, None, 'return')

    def user_exception(self, frame, exc_info):
        exc_type, exc_value, exc_traceback = exc_info
        """This function is called if an exception occurs,
        but only if we are to stop at or just below this level."""
        frame.f_locals['__exception__'] = exc_type, exc_value
        if type(exc_type) == type(''):
            exc_type_name = exc_type
        else: exc_type_name = exc_type.__name__
        self.interaction(frame, exc_traceback, 'exception')


    # General interaction function

    def interaction(self, frame, traceback, event_type):
        self.setup(frame, traceback)
        tos = self.stack[self.curindex]
        top_frame = tos[0]
        lineno = tos[1]

        # don't trace inside of ANY functions that aren't user-written code
        # (e.g., those from imported modules -- e.g., random, re -- or the
        # __restricted_import__ function in this file)
        #
        # empirically, it seems like the FIRST entry in self.stack is
        # the 'run' function from bdb.py, but everything else on the
        # stack is the user program's "real stack"
        for (cur_frame, cur_line) in self.stack[1:]:
          # it seems like user-written code has a filename of '<string>',
          # but maybe there are false positives too?
          if self.canonic(cur_frame.f_code.co_filename) != '<string>':
            return
          # also don't trace inside of the magic "constructor" code
          if cur_frame.f_code.co_name == '__new__':
            return
          # or __repr__, which is often called when running print statements
          if cur_frame.f_code.co_name == '__repr__':
            return


        # debug ...
        #print('===', file=sys.stderr)
        #for (e,ln) in self.stack:
        #  print(e.f_code.co_name + ' ' + e.f_code.co_filename + ' ' + str(ln), file=sys.stderr)
        #print('', file=sys.stderr)


        # don't trace inside of our __restricted_import__ helper function
        # (this check is now subsumed by the above check)
        #if top_frame.f_code.co_name == '__restricted_import__':
        #  return

        self.encoder.reset_heap() # VERY VERY VERY IMPORTANT,
                                  # or else we won't properly capture heap object mutations in the trace!

        if event_type == 'call':
          # Don't be so strict about this assertion because it FAILS
          # when you're calling a generator (not for the first time),
          # since that frame has already previously been on the stack ...
          #assert top_frame not in self.frame_ordered_ids

          self.frame_ordered_ids[top_frame] = self.cur_frame_id
          self.cur_frame_id += 1

          if self.cumulative_mode:
            self.zombie_frames.append(top_frame)


        # only render zombie frames that are NO LONGER on the stack
        cur_stack_frames = [e[0] for e in self.stack]
        zombie_frames_to_render = [e for e in self.zombie_frames if e not in cur_stack_frames]


        # each element is a pair of (function name, ENCODED locals dict)
        encoded_stack_locals = []


        # returns a dict with keys: function name, frame id, id of parent frame, encoded_locals dict
        def create_encoded_stack_entry(cur_frame):
          ret = {}


          parent_frame_id_list = []

          f = cur_frame
          while True:
            p = self.get_parent_frame(f)
            if p:
              pid = self.get_frame_id(p)
              assert pid
              parent_frame_id_list.append(pid)
              f = p
            else:
              break


          cur_name = cur_frame.f_code.co_name

          if cur_name == '':
            cur_name = 'unnamed function'

          # encode in a JSON-friendly format now, in order to prevent ill
          # effects of aliasing later down the line ...
          encoded_locals = {}

          for (k, v) in get_user_locals(cur_frame).items():
            is_in_parent_frame = False

            # don't display locals that appear in your parents' stack frames,
            # since that's redundant
            for pid in parent_frame_id_list:
              parent_frame = self.lookup_zombie_frame_by_id(pid)
              if k in parent_frame.f_locals:
                # ignore __return__, which is never copied
                if k != '__return__':
                  # these values SHOULD BE ALIASES
                  # (don't do an 'is' check since it might not fire for primitives)
                  if parent_frame.f_locals[k] == v:
                      is_in_parent_frame = True

            if is_in_parent_frame and k not in cur_frame.f_code.co_varnames:
              continue

            # don't display some built-in locals ...
            if k == '__module__':
              continue

            encoded_val = self.encoder.encode(v, self.get_parent_of_function)
            encoded_locals[k] = encoded_val


          # order the variable names in a sensible way:

          # Let's start with co_varnames, since it (often) contains all
          # variables in this frame, some of which might not exist yet.
          ordered_varnames = []
          for e in cur_frame.f_code.co_varnames:
            if e in encoded_locals:
              ordered_varnames.append(e)

          # sometimes co_varnames doesn't contain all of the true local
          # variables: e.g., when executing a 'class' definition.  in that
          # case, iterate over encoded_locals and push them onto the end
          # of ordered_varnames in alphabetical order
          for e in sorted(encoded_locals.keys()):
            if e != '__return__' and e not in ordered_varnames:
              ordered_varnames.append(e)

          # finally, put __return__ at the very end
          if '__return__' in encoded_locals:
            ordered_varnames.append('__return__')

          # doctor Python 3 initializer to look like a normal function (denero)
          if '__locals__' in encoded_locals:
            ordered_varnames.remove('__locals__')
            local = encoded_locals.pop('__locals__')
            if encoded_locals.get('__return__', True) is None:
              encoded_locals['__return__'] = local

          # crucial sanity checks!
          assert len(ordered_varnames) == len(encoded_locals)
          for e in ordered_varnames:
            assert e in encoded_locals

          return dict(func_name=cur_name,
                      is_parent=(cur_frame in self.parent_frames_set),
                      frame_id=self.get_frame_id(cur_frame),
                      parent_frame_id_list=parent_frame_id_list,
                      encoded_locals=encoded_locals,
                      ordered_varnames=ordered_varnames)


        i = self.curindex

        # look for whether a nested function has been defined during
        # this particular call:
        if i > 1: # i == 1 implies that there's only a global scope visible
          for v in visit_all_locally_reachable_function_objs(top_frame):
            if (v not in self.closures and \
                v not in self.globally_defined_funcs):

              # Look for the presence of the code object (v.func_code
              # for Python 2 or v.__code__ for Python 3) in the
              # constant pool (f_code.co_consts) of an enclosing
              # stack frame, and set that frame as your parent.
              #
              # This technique properly handles lambdas passed as
              # function parameters. e.g., this example:
              #
              # def foo(x):
              #   bar(lambda y: x + y)
              # def bar(a):
              #   print a(20)
              # foo(10)
              chosen_parent_frame = None
              for (my_frame, my_lineno) in self.stack:
                if chosen_parent_frame:
                  break

                for frame_const in my_frame.f_code.co_consts:
                  if frame_const is (v.__code__ if is_python3 else v.func_code):
                    chosen_parent_frame = my_frame
                    break

              assert chosen_parent_frame # I hope this always passes :0

              # this condition should be False for functions declared in global scope ...
              if chosen_parent_frame in self.frame_ordered_ids:
                self.closures[v] = chosen_parent_frame
                self.parent_frames_set.add(chosen_parent_frame) # unequivocally add to this set!!!
                if not chosen_parent_frame in self.zombie_frames:
                  self.zombie_frames.append(chosen_parent_frame)
        else:
          # if there is only a global scope visible ...
          for (k, v) in get_user_globals(top_frame).items():
            if (type(v) in (types.FunctionType, types.MethodType) and \
                v not in self.closures):
              self.globally_defined_funcs.add(v)


        # climb up until you find '<module>', which is (hopefully) the global scope
        while True:
          cur_frame = self.stack[i][0]
          cur_name = cur_frame.f_code.co_name
          if cur_name == '<module>':
            break

          encoded_stack_locals.append(create_encoded_stack_entry(cur_frame))
          i -= 1

        zombie_encoded_stack_locals = [create_encoded_stack_entry(e) for e in zombie_frames_to_render]


        # encode in a JSON-friendly format now, in order to prevent ill
        # effects of aliasing later down the line ...
        encoded_globals = {}
        for (k, v) in get_user_globals(tos[0]).items():
          encoded_val = self.encoder.encode(v, self.get_parent_of_function)
          encoded_globals[k] = encoded_val

          if k not in self.all_globals_in_order:
            self.all_globals_in_order.append(k)

        # filter out globals that don't exist at this execution point
        # (because they've been, say, deleted with 'del')
        ordered_globals = [e for e in self.all_globals_in_order if e in encoded_globals]
        assert len(ordered_globals) == len(encoded_globals)


        # merge zombie_encoded_stack_locals and encoded_stack_locals
        # into one master ordered list using some simple rules for
        # making it look aesthetically pretty
        stack_to_render = [];

        # first push all regular stack entries
        if encoded_stack_locals:
          for e in encoded_stack_locals:
            e['is_zombie'] = False
            e['is_highlighted'] = False
            stack_to_render.append(e)

          # highlight the top-most active stack entry
          stack_to_render[0]['is_highlighted'] = True


        # now push all zombie stack entries
        for e in zombie_encoded_stack_locals:
          # don't display return value for zombie frames
          # TODO: reconsider ...
          '''
          try:
            e['ordered_varnames'].remove('__return__')
          except ValueError:
            pass
          '''

          e['is_zombie'] = True
          e['is_highlighted'] = False # never highlight zombie entries

          stack_to_render.append(e)

        # now sort by frame_id since that sorts frames in "chronological
        # order" based on the order they were invoked
        stack_to_render.sort(key=lambda e: e['frame_id'])



        # create a unique hash for this stack entry, so that the
        # frontend can uniquely identify it when doing incremental
        # rendering. the strategy is to use a frankenstein-like mix of the
        # relevant fields to properly disambiguate closures and recursive
        # calls to the same function
        for e in stack_to_render:
          hash_str = e['func_name']
          # frame_id is UNIQUE, so it can disambiguate recursive calls
          hash_str += '_f' + str(e['frame_id'])

          # needed to refresh GUI display ...
          if e['is_parent']:
            hash_str += '_p'

          # TODO: this is no longer needed, right? (since frame_id is unique)
          #if e['parent_frame_id_list']:
          #  hash_str += '_p' + '_'.join([str(i) for i in e['parent_frame_id_list']])
          if e['is_zombie']:
            hash_str += '_z'

          e['unique_hash'] = hash_str


        trace_entry = dict(line=lineno,
                           event=event_type,
                           func_name=tos[0].f_code.co_name,
                           globals=encoded_globals,
                           ordered_globals=ordered_globals,
                           stack_to_render=stack_to_render,
                           heap=self.encoder.get_heap(),
                           stdout='')
                           # stdout=get_user_stdout(tos[0]))

        # if there's an exception, then record its info:
        if event_type == 'exception':
          # always check in f_locals
          exc = frame.f_locals['__exception__']
          trace_entry['exception_msg'] = exc[0].__name__ + ': ' + str(exc[1])

        self.trace.append(trace_entry)


        # sanity check to make sure the state of the world at a 'call' instruction
        # is identical to that at the instruction immediately following it ...
        '''
        if len(self.trace) > 1:
          cur = self.trace[-1]
          prev = self.trace[-2]
          if prev['event'] == 'call':
            assert cur['globals'] == prev['globals']
            for (s1, s2) in zip(cur['stack_to_render'], prev['stack_to_render']):
              assert s1 == s2
            assert cur['heap'] == prev['heap']
            assert cur['stdout'] == prev['stdout']
        '''


        if len(self.trace) >= MAX_EXECUTED_LINES:
          self.trace.append(dict(event='instruction_limit_reached', exception_msg='(stopped after ' + str(MAX_EXECUTED_LINES) + ' steps to prevent possible infinite loop)'))
          self.force_terminate()

        self.forget()


    def _runscript(self, script_str, localns, globalns):
        self.executed_script = script_str

        # When bdb sets tracing, a number of call and line events happens
        # BEFORE debugger even reaches user's code (and the exact sequence of
        # events depends on python version). So we take special measures to
        # avoid stopping before we reach the main script (see user_line and
        # user_call for details).
        self._wait_for_mainpyfile = 1


        # ok, let's try to sorta 'sandbox' the user script by not
        # allowing certain potentially dangerous operations.
        # user_builtins = {}

        # ugh, I can't figure out why in Python 2, __builtins__ seems to
        # be a dict, but in Python 3, __builtins__ seems to be a module,
        # so just handle both cases ... UGLY!
        # if type(__builtins__) is dict:
        #   builtin_items = __builtins__.items()
        # else:
        #   assert type(__builtins__) is types.ModuleType
        #   builtin_items = []
        #   for k in dir(__builtins__):
        #     builtin_items.append((k, getattr(__builtins__, k)))

        # for (k, v) in builtin_items:
        #   if k in BANNED_BUILTINS:
        #     continue
        #   elif k == '__import__':
        #     user_builtins[k] = __restricted_import__
        #   else:
        #     user_builtins[k] = v
        # 
        # 
        # user_stdout = cStringIO.StringIO()
        # 
        # sys.stdout = user_stdout
        # user_globals = {"__name__"    : "__main__",
        #                 "__builtins__" : user_builtins,
        #                 "__user_stdout__" : user_stdout}

        try:
          # enforce resource limits RIGHT BEFORE running script_str

          # set ~200MB virtual memory limit AND a 5-second CPU time
          # limit (tuned for Webfaction shared hosting) to protect against
          # memory bombs such as:
          #   x = 2
          #   while True: x = x*x
          # if resource_module_loaded:
          #   resource.setrlimit(resource.RLIMIT_AS, (200000000, 200000000))
          #   resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
          # 
          #   # protect against unauthorized filesystem accesses ...
          #   resource.setrlimit(resource.RLIMIT_NOFILE, (0, 0)) # no opened files allowed

            # VERY WEIRD. If you activate this resource limitation, it
            # ends up generating an EMPTY trace for the following program:
            #   "x = 0\nfor i in range(10):\n  x += 1\n   print x\n  x += 1\n"
            # (at least on my Webfaction hosting with Python 2.7)
            #resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))  # (redundancy for paranoia)

            # sys.modules contains an in-memory cache of already-loaded
            # modules, so if you delete modules from here, they will
            # need to be re-loaded from the filesystem.
            #
            # Thus, as an extra precaution, remove these modules so that
            # they can't be re-imported without opening a new file,
            # which is disallowed by resource.RLIMIT_NOFILE
            #
            # Of course, this isn't a foolproof solution by any means,
            # and it might lead to UNEXPECTED FAILURES later in execution.
            # del sys.modules['os']
            # del sys.modules['sys']

          self.run(script_str, localns, globalns)
        # sys.exit ...
        except SystemExit:
          #sys.exit(0)
          raise bdb.BdbQuit
        except:
          if DEBUG:
            traceback.print_exc()

          trace_entry = dict(event='uncaught_exception')

          (exc_type, exc_val, exc_tb) = sys.exc_info()
          if hasattr(exc_val, 'lineno'):
            trace_entry['line'] = exc_val.lineno
          if hasattr(exc_val, 'offset'):
            trace_entry['offset'] = exc_val.offset

          trace_entry['exception_msg'] = type(exc_val).__name__ + ": " +  str(exc_val)

          # SUPER SUBTLE! if this exact same exception has already been
          # recorded by the program, then DON'T record it again as an
          # uncaught_exception
          already_caught = False
          for e in self.trace:
            if e['event'] == 'exception' and e['exception_msg'] == trace_entry['exception_msg']:
              already_caught = True
              break

          if not already_caught:
            self.trace.append(trace_entry)

          raise bdb.BdbQuit # need to forceably STOP execution


    def force_terminate(self):
      #self.finalize()
      raise bdb.BdbQuit # need to forceably STOP execution


    def finalize(self):
      # sys.stdout = self.GAE_STDOUT # very important!

      assert len(self.trace) <= (MAX_EXECUTED_LINES + 1)

      # don't do this anymore ...
      '''
      # filter all entries after 'return' from '<module>', since they
      # seem extraneous:
      res = []
      for e in self.trace:
        res.append(e)
        if e['event'] == 'return' and e['func_name'] == '<module>':
          break
      '''

      res = self.trace

      # if the SECOND to last entry is an 'exception'
      # and the last entry is return from <module>, then axe the last
      # entry, for aesthetic reasons :)
      if len(res) >= 2 and \
         res[-2]['event'] == 'exception' and \
         res[-1]['event'] == 'return' and res[-1]['func_name'] == '<module>':
        res.pop()

      self.trace = res

      self.finalizer_func(self.executed_script, self.trace)



# the MAIN meaty function!!!
def exec_script_str(script_str, cumulative_mode, finalizer_func, localns, globalns):
  logger = PGLogger(cumulative_mode, finalizer_func)

  try:
    logger._runscript(script_str, localns, globalns)
  except bdb.BdbQuit:
    pass
  finally:
    logger.finalize()

