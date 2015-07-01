# encoding: utf-8
"""
Enable tk to be used interacive by setting PyOS_InputHook.
"""
import _tkinter

def inputhook_tk(app, inputhook_context):
    # Add a handler that sets the stop flag when `prompt-toolkit` has input to
    # process.
    stop = [False]
    def done(*a):
        stop[0] = True

    app.createfilehandler(inputhook_context.fileno(), _tkinter.READABLE, done)

    # Run the TK event loop as long as we don't receive input.
    while app.tk.dooneevent(_tkinter.ALL_EVENTS):
        if stop[0]:
            break

    app.deletefilehandler(inputhook_context.fileno())
