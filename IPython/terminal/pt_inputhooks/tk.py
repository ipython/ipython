# Code borrowed from ptpython
# https://github.com/jonathanslenders/ptpython/blob/86b71a89626114b18898a0af463978bdb32eeb70/ptpython/eventloop.py

# Copyright (c) 2015, Jonathan Slenders
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice, this
#   list of conditions and the following disclaimer in the documentation and/or
#   other materials provided with the distribution.
#
# * Neither the name of the {organization} nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Wrapper around the eventloop that gives some time to the Tkinter GUI to process
events when it's loaded and while we are waiting for input at the REPL. This
way we don't block the UI of for instance ``turtle`` and other Tk libraries.

(Normally Tkinter registers it's callbacks in ``PyOS_InputHook`` to integrate
in readline. ``prompt-toolkit`` doesn't understand that input hook, but this
will fix it for Tk.)
"""
import sys
import time
import select

import _tkinter
import tkinter

def inputhook(inputhook_context):
    """
    Inputhook for Tk.
    Run the Tk eventloop until prompt-toolkit needs to process the next input.
    """
    # Get the current TK application.
    root = tkinter._default_root

    def wait_using_select():
        """
        Run the Tk eventloop until the file that we got from the
        inputhook context becomes readable.
        """
        # Run the TK event loop as long as we don't receive input.
        while True:
            while root.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
                pass
            if select.select([inputhook_context.fileno()], [], [], 0):
                break

    def wait_using_polling():
        """
        For Windows, run the Tk eventloop and poll until input is ready.
        """
        while not inputhook_context.input_is_ready():
            while root.dooneevent(_tkinter.ALL_EVENTS | _tkinter.DONT_WAIT):
                 pass
            # Sleep to make the CPU idle, but not too long, so that the UI
            # stays responsive.
            time.sleep(.01)

    if root is not None:
        if sys.platform == "win32":
            wait_using_polling()
        else:
            wait_using_select()
