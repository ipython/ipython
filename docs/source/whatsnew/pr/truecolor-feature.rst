prompt_toolkit uses pygments styles for syntax highlighting. By default, the
colors specified in the style are approximated using a standard 256-color
palette. prompt_toolkit also supports 24bit, a.k.a. "true", a.k.a. 16-million
color escape sequences which enable compatible terminals to display the exact
colors specified instead of an approximation. This true_color option exposes
that capability in prompt_toolkit to the IPython shell.

Here is a good source for the current state of true color support in various
terminal emulators and software projects: https://gist.github.com/XVilka/8346728
