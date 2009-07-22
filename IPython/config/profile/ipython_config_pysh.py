from ipython_config import *

EXECUTE.insert(0, 'from IPython.extensions.InterpreterExec import *')

PROMPT_IN1 = '\C_LightGreen\u@\h\C_LightBlue[\C_LightCyan\Y1\C_LightBlue]\C_Green|\#> '
PROMPT_IN2 = '\C_Green|\C_LightGreen\D\C_Green> '
PROMPT_OUT = '<\#> '

PROMPTS_PAD_LEFT = True

SEPARATE_IN = 0
SEPARATE_OUT = 0
SEPARATE_OUT2 = 0

MULTI_LINE_SPECIALS = True