# This can be used at any point in a config file to load a sub config
# and merge it into the current one.
load_subconfig('ipython_config.py')

InteractiveShell.prompt_in1 = '\C_LightGreen\u@\h\C_LightBlue[\C_LightCyan\Y1\C_LightBlue]\C_Green|\#> '
InteractiveShell.prompt_in2 = '\C_Green|\C_LightGreen\D\C_Green> '
InteractiveShell.prompt_out = '<\#> '

InteractiveShell.prompts_pad_left = True

InteractiveShell.separate_in = ''
InteractiveShell.separate_out = ''
InteractiveShell.separate_out2 = ''

PrefilterManager.multi_line_specials = True

lines = """
%rehashx
"""

# You have to make sure that attributes that are containers already
# exist before using them.  Simple assigning a new list will override
# all previous values.
if hasattr(Global, 'exec_lines'):
    Global.exec_lines.append(lines)
else:
    Global.exec_lines = [lines]