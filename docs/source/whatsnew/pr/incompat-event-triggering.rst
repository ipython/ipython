Update IPython event triggering to ensure callback registration and
unregistration only affects the set of callbacks the *next* time that event is
triggered. See :ghissue:`9447` and :ghpull:`9453`.

This is a change to the existing semantics, wherein one callback registering a
second callback when triggered for an event would previously be invoked for
that same event.
