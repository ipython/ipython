Prompt Rendering Performance improvements
=========================================

Pull Request :ghpull:`11933` introduced an optimisation in the prompt rendering
logic that should decrease the resource usage of IPython when using the
_default_ configuration but could potentially introduce a regression of
functionalities if you are using a custom prompt.

We know assume if you haven't changed the default keybindings that the prompt
**will not change** during the duration of your input – which is for example
not true when using vi insert mode that switches between `[ins]` and `[nor]`
for the current mode.

If you are experiencing any issue let us know.
