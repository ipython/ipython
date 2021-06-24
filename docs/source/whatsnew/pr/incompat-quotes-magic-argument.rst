Incompatible change to the way magics handle spaces and quotes
--------------------------------------------------------------

Magics that previously split on whitespace for arguments now preserve
backslash-escaped whitespace and whitespace inside of quotes. This allows for
filenames that have spaces to be treated the same as files without spaces.
However, this change is backwards incompatible with previous behavior of
preserving un-escaped quotes in the `writefile` magic, for example.

So if you previously had code like

`%%writefile File"With"Quotes`

You must now write

`%%writefile 'File"With"Quotes`

or 

`%%writefile File\"With\"Quotes'`


It was also the case that, due to some special-casing, surrounding quotes for
a filename containing spaces for writefile did work (`%%writefile "File with
spaces"`), the escaping of the same file name did not (`%%writefile File\
with\ spaces` would fail with "UsageError: unrecognized arguments: with\
spaces"). Now, both cases work the same.

The underlying change was to have
:meth:`~IPython.core.magics_arguments.parse_argstring` pass `posix=True` and
`strict=False` when calling `arg_split`.

This change fixes :ghissue:`12729`, for full details, please see
:ghpull:`13027`

