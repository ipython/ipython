c = get_config()

# This can be used at any point in a config file to load a sub config
# and merge it into the current one.
load_subconfig('ipython_config.py')

c.InteractiveShell.prompt_in1 = '\C_LightGreen\u@\h\C_LightBlue[\C_LightCyan\Y1\C_LightBlue]\C_Green|\#> '
c.InteractiveShell.prompt_in2 = '\C_Green|\C_LightGreen\D\C_Green> '
c.InteractiveShell.prompt_out = '<\#> '

c.InteractiveShell.prompts_pad_left = True

c.InteractiveShell.separate_in = ''
c.InteractiveShell.separate_out = ''
c.InteractiveShell.separate_out2 = ''

c.PrefilterManager.multi_line_specials = True

lines = """
%rehashx
"""

# You have to make sure that attributes that are containers already
# exist before using them.  Simple assigning a new list will override
# all previous values.
if hasattr(c.Global, 'exec_lines'):
    c.Global.exec_lines.append(lines)
else:
    c.Global.exec_lines = [lines]