Added the ability to add parameters to alias_magic.

e.g.:

In [2]: %alias_magic hist history --params "-l 2" --line
Created `%hist` as an alias for `%history -l 2`.

In [3]: hist
%alias_magic hist history --params "-l 30" --line
%alias_magic hist history --params "-l 2" --line

Previously it was only possible to have an alias attached to a single function, and you would have to pass in the given parameters every time.

e.g.:

In [4]: %alias_magic hist history --line
Created `%hist` as an alias for `%history`.

In [5]: hist -l 2
hist
%alias_magic hist history --line

