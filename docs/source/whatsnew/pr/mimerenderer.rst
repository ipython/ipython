Arbitrary Mimetypes Handing in Terminal
=======================================

When using IPython terminal it is now possible to register function to handle
arbitrary mimetypes. While rendering non-text based representation was possible in
many jupyter frontend; it was not possible in terminal IPython, as usually
terminal are limited to displaying text. As many terminal these days provide
escape sequences to display non-text; bringing this loved feature to IPython CLI
made a lot of sens. This functionality will not only allow inline images; but
allow opening of external program; for example ``mplayer`` to "display" sound
files.

So far only the hooks necessary for this are in place, but no default mime
renderers added; so inline images will only be available via extensions. We will
progressively enable these features by default in the next few releases, and
contribution is welcomed.

We welcome any feedback on the API. See :ref:`shell_mimerenderer` for more
informations.
