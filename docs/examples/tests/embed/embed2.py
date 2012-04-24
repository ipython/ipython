"""This tests passing a dict for the user_ns at shell instantiation."""
from IPython import embed

user_ns = dict(cookie='monster')
embed(user_ns=user_ns, banner1="check 'cookie' present, locals and globals equivalent")
