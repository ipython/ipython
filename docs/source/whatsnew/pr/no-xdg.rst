* Previous versions of IPython on Linux would use the XDG config directory,
  creating :file:`~/.config/ipython` by default. We have decided to go
  back to :file:`~/.ipython` for consistency among systems. IPython will
  issue a warning if it finds the XDG location, and will move it to the new
  location if there isn't already a directory there.
