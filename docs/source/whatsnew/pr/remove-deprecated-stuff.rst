Remove Deprecated Stuff
================================

We no longer need to add `extensions` to the PYTHONPATH because that is being
handled by `load_extension`.

We are also removing Cythonmagic, sympyprinting and rmagic as they are now in
other packages and no longer need to be inside IPython.
