c = get_config()

# If the master config file uses syntax that's invalid in Python 3, we'll skip
# it and just use the factory defaults.
try:
    load_subconfig('ipython_config.py', profile='default')
except Exception:
    pass
else:
    # We reset exec_lines in case they're not compatible with Python 3.
    c.InteractiveShellApp.exec_lines = []
