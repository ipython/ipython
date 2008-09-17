# encoding: utf-8 -*- test-case-name:
# FIXME: Need to add tests.
# ipython1.frontend.wx.tests.test_wx_frontend -*-

"""Classes to provide a Wx frontend to the
IPython.kernel.core.interpreter.

This class inherits from ConsoleWidget, that provides a console-like
widget to provide a text-rendering widget suitable for a terminal.
"""

__docformat__ = "restructuredtext en"

#-------------------------------------------------------------------------------
#       Copyright (C) 2008  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# Imports
#-------------------------------------------------------------------------------

# Major library imports
import re
import __builtin__
from time import sleep
import sys
from threading import Lock
import string

import wx
from wx import stc

# Ipython-specific imports.
from IPython.frontend._process import PipedProcess
from console_widget import ConsoleWidget
from IPython.frontend.prefilterfrontend import PrefilterFrontEnd

#-------------------------------------------------------------------------------
# Constants 
#-------------------------------------------------------------------------------

_COMPLETE_BUFFER_BG = '#FAFAF1' # Nice green
_INPUT_BUFFER_BG = '#FDFFD3' # Nice yellow
_ERROR_BG = '#FFF1F1' # Nice red

_COMPLETE_BUFFER_MARKER = 31
_ERROR_MARKER = 30
_INPUT_MARKER = 29

prompt_in1 = \
        '\n\x01\x1b[0;34m\x02In [\x01\x1b[1;34m\x02$number\x01\x1b[0;34m\x02]: \x01\x1b[0m\x02'

prompt_out = \
    '\x01\x1b[0;31m\x02Out[\x01\x1b[1;31m\x02$number\x01\x1b[0;31m\x02]: \x01\x1b[0m\x02'

#-------------------------------------------------------------------------------
# Classes to implement the Wx frontend
#-------------------------------------------------------------------------------
class WxController(ConsoleWidget, PrefilterFrontEnd):
    """Classes to provide a Wx frontend to the
    IPython.kernel.core.interpreter.

    This class inherits from ConsoleWidget, that provides a console-like
    widget to provide a text-rendering widget suitable for a terminal.
    """

    output_prompt_template = string.Template(prompt_out)

    input_prompt_template = string.Template(prompt_in1)

    # Print debug info on what is happening to the console.
    debug = False

    # The title of the terminal, as captured through the ANSI escape
    # sequences.
    def _set_title(self, title):
            return self.Parent.SetTitle(title)

    def _get_title(self):
            return self.Parent.GetTitle()

    title = property(_get_title, _set_title)


    # The buffer being edited.
    # We are duplicating the definition here because of multiple
    # inheritence
    def _set_input_buffer(self, string):
        ConsoleWidget._set_input_buffer(self, string)
        self._colorize_input_buffer()

    def _get_input_buffer(self):
        """ Returns the text in current edit buffer.
        """
        return ConsoleWidget._get_input_buffer(self)

    input_buffer = property(_get_input_buffer, _set_input_buffer)


    #--------------------------------------------------------------------------
    # Private Attributes
    #--------------------------------------------------------------------------

    # A flag governing the behavior of the input. Can be:
    #
    #       'readline' for readline-like behavior with a prompt 
    #            and an edit buffer.
    #       'raw_input' similar to readline, but triggered by a raw-input
    #           call. Can be used by subclasses to act differently.
    #       'subprocess' for sending the raw input directly to a
    #           subprocess.
    #       'buffering' for buffering of the input, that will be used
    #           when the input state switches back to another state.
    _input_state = 'readline'

    # Attribute to store reference to the pipes of a subprocess, if we
    # are running any.
    _running_process = False

    # A queue for writing fast streams to the screen without flooding the
    # event loop
    _out_buffer = []

    # A lock to lock the _out_buffer to make sure we don't empty it
    # while it is being swapped
    _out_buffer_lock = Lock()

    # The different line markers used to higlight the prompts.
    _markers = dict()

    #--------------------------------------------------------------------------
    # Public API
    #--------------------------------------------------------------------------
 
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=wx.CLIP_CHILDREN|wx.WANTS_CHARS,
                 *args, **kwds):
        """ Create Shell instance.
        """
        ConsoleWidget.__init__(self, parent, id, pos, size, style)
        PrefilterFrontEnd.__init__(self, **kwds)
        
        # Stick in our own raw_input:
        self.ipython0.raw_input = self.raw_input

        # Marker for complete buffer.
        self.MarkerDefine(_COMPLETE_BUFFER_MARKER, stc.STC_MARK_BACKGROUND,
                                background=_COMPLETE_BUFFER_BG)
        # Marker for current input buffer.
        self.MarkerDefine(_INPUT_MARKER, stc.STC_MARK_BACKGROUND,
                                background=_INPUT_BUFFER_BG)
        # Marker for tracebacks.
        self.MarkerDefine(_ERROR_MARKER, stc.STC_MARK_BACKGROUND,
                                background=_ERROR_BG)

        # A time for flushing the write buffer
        BUFFER_FLUSH_TIMER_ID = 100
        self._buffer_flush_timer = wx.Timer(self, BUFFER_FLUSH_TIMER_ID)
        wx.EVT_TIMER(self, BUFFER_FLUSH_TIMER_ID, self._buffer_flush)

        if 'debug' in kwds:
            self.debug = kwds['debug']
            kwds.pop('debug')

        # Inject self in namespace, for debug
        if self.debug:
            self.shell.user_ns['self'] = self
        # Inject our own raw_input in namespace
        self.shell.user_ns['raw_input'] = self.raw_input


    def raw_input(self, prompt=''):
        """ A replacement from python's raw_input.
        """
        self.new_prompt(prompt)
        self._input_state = 'raw_input'
        if hasattr(self, '_cursor'):
            del self._cursor 
        self.SetCursor(wx.StockCursor(wx.CURSOR_CROSS))
        self.__old_on_enter = self._on_enter
        event_loop = wx.EventLoop()
        def my_on_enter():
            event_loop.Exit()
        self._on_enter = my_on_enter
        # XXX: Running a separate event_loop. Ugly.
        event_loop.Run() 
        self._on_enter = self.__old_on_enter
        self._input_state = 'buffering'
        self._cursor = wx.BusyCursor()
        return self.input_buffer.rstrip('\n')


    def system_call(self, command_string):
        self._input_state = 'subprocess'
        event_loop = wx.EventLoop()
        def _end_system_call():
            self._input_state = 'buffering'
            self._running_process = False
            event_loop.Exit()

        self._running_process = PipedProcess(command_string, 
                    out_callback=self.buffered_write,
                    end_callback = _end_system_call)
        self._running_process.start()
        # XXX: Running a separate event_loop. Ugly.
        event_loop.Run() 
        # Be sure to flush the buffer.
        self._buffer_flush(event=None)


    def do_calltip(self):
        """ Analyse current and displays useful calltip for it.
        """
        if self.debug:
            print >>sys.__stdout__, "do_calltip" 
        separators =  re.compile('[\s\{\}\[\]\(\)\= ,:]')
        symbol = self.input_buffer
        symbol_string = separators.split(symbol)[-1]
        base_symbol_string = symbol_string.split('.')[0]
        if base_symbol_string in self.shell.user_ns:
            symbol = self.shell.user_ns[base_symbol_string]
        elif base_symbol_string in self.shell.user_global_ns:
            symbol = self.shell.user_global_ns[base_symbol_string]
        elif base_symbol_string in __builtin__.__dict__:
            symbol = __builtin__.__dict__[base_symbol_string]
        else:
            return False
        try:
            for name in symbol_string.split('.')[1:] + ['__doc__']:
                symbol = getattr(symbol, name)
            self.AutoCompCancel()
            # Check that the symbol can indeed be converted to a string:
            symbol += ''
            wx.CallAfter(self.CallTipShow, self.GetCurrentPos(), symbol)
        except:
            # The retrieve symbol couldn't be converted to a string
            pass


    def _popup_completion(self, create=False):
        """ Updates the popup completion menu if it exists. If create is 
            true, open the menu.
        """
        if self.debug:
            print >>sys.__stdout__, "_popup_completion" 
        line = self.input_buffer
        if (self.AutoCompActive() and line and not line[-1] == '.') \
                    or create==True:
            suggestion, completions = self.complete(line)
            offset=0
            if completions:
                complete_sep =  re.compile('[\s\{\}\[\]\(\)\= ,:]')
                residual = complete_sep.split(line)[-1]
                offset = len(residual)
                self.pop_completion(completions, offset=offset)
                if self.debug:
                    print >>sys.__stdout__, completions 


    def buffered_write(self, text):
        """ A write method for streams, that caches the stream in order
            to avoid flooding the event loop.

            This can be called outside of the main loop, in separate
            threads.
        """
        self._out_buffer_lock.acquire()
        self._out_buffer.append(text)
        self._out_buffer_lock.release()
        if not self._buffer_flush_timer.IsRunning():
            wx.CallAfter(self._buffer_flush_timer.Start, 
                                        milliseconds=100, oneShot=True)


    #--------------------------------------------------------------------------
    # LineFrontEnd interface 
    #--------------------------------------------------------------------------
 
    def execute(self, python_string, raw_string=None):
        self._input_state = 'buffering'
        self.CallTipCancel()
        self._cursor = wx.BusyCursor()
        if raw_string is None:
            raw_string = python_string
        end_line = self.current_prompt_line \
                        + max(1,  len(raw_string.split('\n'))-1)
        for i in range(self.current_prompt_line, end_line):
            if i in self._markers:
                self.MarkerDeleteHandle(self._markers[i])
            self._markers[i] = self.MarkerAdd(i, _COMPLETE_BUFFER_MARKER)
        # Use a callafter to update the display robustly under windows
        def callback():
            self.GotoPos(self.GetLength())
            PrefilterFrontEnd.execute(self, python_string, 
                                            raw_string=raw_string)
        wx.CallAfter(callback)

    def save_output_hooks(self):    
        self.__old_raw_input = __builtin__.raw_input
        PrefilterFrontEnd.save_output_hooks(self)

    def capture_output(self):
        self.SetLexer(stc.STC_LEX_NULL)
        PrefilterFrontEnd.capture_output(self)
        __builtin__.raw_input = self.raw_input
        
    
    def release_output(self):
        __builtin__.raw_input = self.__old_raw_input
        PrefilterFrontEnd.release_output(self)
        self.SetLexer(stc.STC_LEX_PYTHON)


    def after_execute(self):
        PrefilterFrontEnd.after_execute(self)
        # Clear the wait cursor
        if hasattr(self, '_cursor'):
            del self._cursor
        self.SetCursor(wx.StockCursor(wx.CURSOR_CHAR))


    def show_traceback(self):
        start_line = self.GetCurrentLine()
        PrefilterFrontEnd.show_traceback(self)
        self.ProcessEvent(wx.PaintEvent())
        #wx.Yield()
        for i in range(start_line, self.GetCurrentLine()):
            self._markers[i] = self.MarkerAdd(i, _ERROR_MARKER)

    
    #--------------------------------------------------------------------------
    # FrontEndBase interface 
    #--------------------------------------------------------------------------
    
    def render_error(self, e):
        start_line = self.GetCurrentLine()
        self.write('\n' + e + '\n')
        for i in range(start_line, self.GetCurrentLine()):
            self._markers[i] = self.MarkerAdd(i, _ERROR_MARKER)


    #--------------------------------------------------------------------------
    # ConsoleWidget interface 
    #--------------------------------------------------------------------------

    def new_prompt(self, prompt):
        """ Display a new prompt, and start a new input buffer.
        """
        self._input_state = 'readline'
        ConsoleWidget.new_prompt(self, prompt)
        i = self.current_prompt_line
        self._markers[i] = self.MarkerAdd(i, _INPUT_MARKER)


    def write(self, *args, **kwargs):
        # Avoid multiple inheritence, be explicit about which
        # parent method class gets called
        ConsoleWidget.write(self, *args, **kwargs)


    def _on_key_down(self, event, skip=True):
        """ Capture the character events, let the parent
            widget handle them, and put our logic afterward.
        """
        # FIXME: This method needs to be broken down in smaller ones.
        current_line_number = self.GetCurrentLine()
        if event.KeyCode in (ord('c'), ord('C')) and event.ControlDown():
            # Capture Control-C
            if self._input_state == 'subprocess':
                if self.debug:
                    print >>sys.__stderr__, 'Killing running process'
                if hasattr(self._running_process, 'process'):
                    self._running_process.process.kill()
            elif self._input_state == 'buffering':
                if self.debug:
                    print >>sys.__stderr__, 'Raising KeyboardInterrupt'
                raise KeyboardInterrupt
                # XXX: We need to make really sure we
                # get back to a prompt.
        elif self._input_state == 'subprocess' and (
                ( event.KeyCode<256 and
                        not event.ControlDown() )
                    or 
                ( event.KeyCode in (ord('d'), ord('D')) and
                  event.ControlDown())):
            #  We are running a process, we redirect keys.
            ConsoleWidget._on_key_down(self, event, skip=skip)
            char = chr(event.KeyCode)
            # Deal with some inconsistency in wx keycodes:
            if char == '\r':
                char = '\n'
            elif not event.ShiftDown():
                char = char.lower()
            if event.ControlDown() and event.KeyCode in (ord('d'), ord('D')):
                char = '\04'
            self._running_process.process.stdin.write(char)
            self._running_process.process.stdin.flush()
        elif event.KeyCode in (ord('('), 57, 53):
            # Calltips
            event.Skip()
            self.do_calltip()
        elif self.AutoCompActive() and not event.KeyCode == ord('\t'):
            event.Skip()
            if event.KeyCode in (wx.WXK_BACK, wx.WXK_DELETE): 
                wx.CallAfter(self._popup_completion, create=True)
            elif not event.KeyCode in (wx.WXK_UP, wx.WXK_DOWN, wx.WXK_LEFT,
                            wx.WXK_RIGHT, wx.WXK_ESCAPE):
                wx.CallAfter(self._popup_completion)
        else:
            # Up history
            if event.KeyCode == wx.WXK_UP and (
                    ( current_line_number == self.current_prompt_line and
                        event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN) ) 
                    or event.ControlDown() ):
                new_buffer = self.get_history_previous(
                                            self.input_buffer)
                if new_buffer is not None:
                    self.input_buffer = new_buffer
                    if self.GetCurrentLine() > self.current_prompt_line:
                        # Go to first line, for seemless history up.
                        self.GotoPos(self.current_prompt_pos)
            # Down history
            elif event.KeyCode == wx.WXK_DOWN and (
                    ( current_line_number == self.LineCount -1 and
                        event.Modifiers in (wx.MOD_NONE, wx.MOD_WIN) ) 
                    or event.ControlDown() ):
                new_buffer = self.get_history_next()
                if new_buffer is not None:
                    self.input_buffer = new_buffer
            # Tab-completion
            elif event.KeyCode == ord('\t'):
                current_line, current_line_number = self.CurLine
                if not re.match(r'^\s*$', current_line):
                    self.complete_current_input()
                    if self.AutoCompActive():
                        wx.CallAfter(self._popup_completion, create=True)
                else:
                    event.Skip()
            else:
                ConsoleWidget._on_key_down(self, event, skip=skip)


    def _on_key_up(self, event, skip=True):
        """ Called when any key is released.
        """
        if event.KeyCode in (59, ord('.')):
            # Intercepting '.'
            event.Skip()
            wx.CallAfter(self._popup_completion, create=True)
        else:
            ConsoleWidget._on_key_up(self, event, skip=skip)


    def _on_enter(self):
        """ Called on return key down, in readline input_state.
        """
        if self.debug:
            print >>sys.__stdout__, repr(self.input_buffer)
        PrefilterFrontEnd._on_enter(self)


    #--------------------------------------------------------------------------
    # EditWindow API
    #--------------------------------------------------------------------------

    def OnUpdateUI(self, event):
        """ Override the OnUpdateUI of the EditWindow class, to prevent 
            syntax highlighting both for faster redraw, and for more
            consistent look and feel.
        """
        if not self._input_state == 'readline':
            ConsoleWidget.OnUpdateUI(self, event)

    #--------------------------------------------------------------------------
    # Private API
    #--------------------------------------------------------------------------
 
    def _buffer_flush(self, event):
        """ Called by the timer to flush the write buffer.
            
            This is always called in the mainloop, by the wx timer.
        """
        self._out_buffer_lock.acquire()
        _out_buffer = self._out_buffer
        self._out_buffer = []
        self._out_buffer_lock.release()
        self.write(''.join(_out_buffer), refresh=False)


    def _colorize_input_buffer(self):
        """ Keep the input buffer lines at a bright color.
        """
        if not self._input_state in ('readline', 'raw_input'):
            return
        end_line = self.GetCurrentLine()
        if not sys.platform == 'win32':
            end_line += 1
        for i in range(self.current_prompt_line, end_line):
            if i in self._markers:
                self.MarkerDeleteHandle(self._markers[i])
            self._markers[i] = self.MarkerAdd(i, _INPUT_MARKER)


if __name__ == '__main__':
    class MainWindow(wx.Frame):
        def __init__(self, parent, id, title):
            wx.Frame.__init__(self, parent, id, title, size=(300,250))
            self._sizer = wx.BoxSizer(wx.VERTICAL)
            self.shell = WxController(self)
            self._sizer.Add(self.shell, 1, wx.EXPAND)
            self.SetSizer(self._sizer)
            self.SetAutoLayout(1)
            self.Show(True)

    app = wx.PySimpleApp()
    frame = MainWindow(None, wx.ID_ANY, 'Ipython')
    frame.shell.SetFocus()
    frame.SetSize((680, 460))
    self = frame.shell

    app.MainLoop()

