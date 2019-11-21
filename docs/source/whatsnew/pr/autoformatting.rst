Code autoformatting
===================

The IPython terminal can now auto format your code just before entering a new
line or executing a command. To do so use the
``--TerminalInteractiveShell.autoformatter`` option and set it to ``'black'``;
if black is installed IPython will use black to format your code when possible. 

IPython cannot always properly format your code; in particular it will
auto formatting with *black* will only work if:

   - Your code does not contains magics or special python syntax. 

   - There is no code after your cursor. 

The Black API is also still in motion; so this may not work with all versions of
black. 

It should be possible to register custom reformatter, though the API is till in
flux. 




