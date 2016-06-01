"""This is an example that shows how to create new prompts for IPython
"""

from IPython.terminal.prompts import Prompts, Token
import os

class MyPrompt(Prompts):

     def in_prompt_tokens(self, cli=None):
         return [(Token, os.getcwd()),
                 (Token.Prompt, '>>>')]

def load_ipython_extension(shell):
    new_prompts = MyPrompt(shell)
    new_prompts.old_prompts = shell.prompts
    shell.prompts = new_prompts

def unload_ipython_extension(shell):
    if not hasattr(shell.prompts, 'old_prompts'):
        print("cannot unload")
    else:
        shell.prompts = shell.prompts.old_prompts




