Extending Configurable Containers
---------------------------------

Some configurable traits are containers (list, dict, set)
Config objects now support calling ``extend``, ``update``, ``insert``, etc.
on traits in config files, which will ultimately result in calling
those methods on the original object.

The effect being that you can now add to containers without having to copy/paste
the initial value::

    c = get_config()
    c.InlineBackend.rc.update({ 'figure.figsize' : (6, 4) })


