"""Terminal input and output prompts."""

from pygments.token import Token
import sys

from IPython.core.displayhook import DisplayHook

from prompt_toolkit.layout.utils import token_list_width

import os
import os.path
import shlex
import subprocess
import tempfile

class Prompts(object):
    def __init__(self, shell):
        self.shell = shell

    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Prompt, 'In ['),
            (Token.PromptNum, str(self.shell.execution_count)),
            (Token.Prompt, ']: '),
        ]

    def _width(self):
        return token_list_width(self.in_prompt_tokens())

    def continuation_prompt_tokens(self, cli=None, width=None):
        if width is None:
            width = self._width()
        return [
            (Token.Prompt, (' ' * (width - 5)) + '...: '),
        ]

    def rewrite_prompt_tokens(self):
        width = self._width()
        return [
            (Token.Prompt, ('-' * (width - 2)) + '> '),
        ]

    def out_prompt_tokens(self):
        return [
            (Token.OutPrompt, 'Out['),
            (Token.OutPromptNum, str(self.shell.execution_count)),
            (Token.OutPrompt, ']: '),
        ]

class ClassicPrompts(Prompts):
    def in_prompt_tokens(self, cli=None):
        return [
            (Token.Prompt, '>>> '),
        ]

    def continuation_prompt_tokens(self, cli=None, width=None):
        return [
            (Token.Prompt, '... ')
        ]

    def rewrite_prompt_tokens(self):
        return []

    def out_prompt_tokens(self):
        return []

class RichPromptDisplayHook(DisplayHook):
    """Subclass of base display hook using coloured prompt"""
    def write_output_prompt(self):
        sys.stdout.write(self.shell.separate_out)
        # If we're not displaying a prompt, it effectively ends with a newline,
        # because the output will be left-aligned.
        self.prompt_end_newline = True

        if self.do_full_cache:
            tokens = self.shell.prompts.out_prompt_tokens()
            prompt_txt = ''.join(s for t, s in tokens)
            if prompt_txt and not prompt_txt.endswith('\n'):
                # Ask for a newline before multiline output
                self.prompt_end_newline = False

            if self.shell.pt_cli:
                self.shell.pt_cli.print_tokens(tokens)
            else:
                sys.stdout.write(prompt_txt)

    def write_format_data(self, format_dict, md_dict=None):
        """Write the format data dict to the frontend.

        This version adds support for image/png if the 
        IPYTHON_IMAGE_VIEWER environment avariable is set.

        Parameters
        ----------
        format_dict : dict
            The format dict for the object passed to `sys.displayhook`.
        md_dict : dict (optional)
            The metadata dict to be associated with the display data.
        """
        image_data = format_dict.get("image/png")
        if image_data is not None and self.view_image(image_data):
            return
        return super().write_format_data(format_dict, md_dict)

    def view_image(self, image_data):
        """Attempt to display the raw image_data .
          image_data should be a `bytes` object containing image data in PNG format

          We will check if the IPYTHON_IMAGE_VIEWER environment variable is set.
          If so, this is used to show the image.
        """
        # Probably not worth caching the image_viewer.
        # Not caching has the advantage that you can set it in a running IPython.
        image_viewer = os.getenv("IPYTHON_IMAGE_VIEWER")
        if image_viewer is None:
            # Environment variable does not exist
            return False
        # We use shlex.split so that IPYTHON_IMAGE_VIEWER can also contain
        # options in addition to the executable.
        image_viewer = shlex.split(image_viewer)
        if not image_viewer:
            # Environment variable existed but was empty
            return False
        with tempfile.TemporaryDirectory() as dirname:
            png_file = os.path.join(dirname, "out.png")
            with open(png_file, "wb") as f:
                f.write(image_data)
            try:
                # We don't want to clutter the display with errors on failure,
                # so redirect stderr to DEVNULL.
                subprocess.check_call(tuple(image_viewer) + (png_file,), stderr=subprocess.DEVNULL)
            except subprocess.SubprocessError:
                return False
        return True
