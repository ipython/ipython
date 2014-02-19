Default Cell Magic
------------------

Use

    %default_cell_magic xyz

to have the `%%xyz` cell magic prepended automatically to all subsequent input cells. See

    %default_cell_magic?

for details.


CoffeeScript Cell Magic
-----------------------

Execute CoffeeScript in the browser. Experience is similar to running python in teh notebook:
results are shown in the notebook, variables can be accessed across cells etc.

Example:

    %%coffee
    console.log "Hello from CoffeeScript!"


Together with

    %default_cell_magic coffee

this can be used to write CoffeeScript notebooks with code being executed in the context of the browser.