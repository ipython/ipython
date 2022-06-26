Fix quiet-mode detection
========================

DisplayHook was inspecting the last stored history to determine whether it should behave as though in quiet mode.
This assumption does not hold when the last execution does not store shell history, e.g. when using a custom
kernel client. This fix just moves the quiet-mode handling to an explicit call from the execution handler.
