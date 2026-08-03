Forcing kitty graphics support on or off
----------------------------------------

IPython decides whether the terminal understands the `kitty graphics protocol
<https://sw.kovidgoyal.net/kitty/graphics-protocol/>`__ by walking up the
process tree looking for a known terminal emulator. That guess can be wrong --
for instance inside ``tmux``, a container, or an emulator not on the list -- and
it is not free: it imports ``psutil`` and inspects the process tree on every
startup that has a tty.

The ``IPYTHON_KITTY_GRAPHICS`` environment variable now states the answer
outright and skips the detection entirely::

    IPYTHON_KITTY_GRAPHICS=1 ipython     # my terminal does support it
    IPYTHON_KITTY_GRAPHICS=0 ipython     # it does not; do not even look

Accepted values are ``1``/``true`` and ``0``/``false``, case-insensitive.
Leaving it unset, or setting it to the empty string, keeps the existing
autodetection. Any other value is ignored with a warning, so a typo cannot
silently turn graphics off.
