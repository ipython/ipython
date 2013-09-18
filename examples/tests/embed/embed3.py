"""This tests passing local_ns and global_ns (for backwards compatibility only)
at activation of an embedded shell."""
from IPython.terminal.embed import InteractiveShellEmbed

user_ns = dict(cookie='monster')
ISE = InteractiveShellEmbed(banner1='check cookie in locals, and globals empty')
ISE(local_ns=user_ns, global_ns={})
