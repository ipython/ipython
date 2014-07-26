git hooks for IPython

add these to your `.git/hooks`

For now, we just have `post-checkout` and `post-merge`,
both of which update submodules and attempt to rebuild css sourcemaps,
so make sure that you have a fully synced repo whenever you checkout or pull.

To use these hooks, run `./install-hooks.sh`. 
If you havn't initialised and updated the submodules manually, you will then need to run `git checkout master` to activate the hooks (even if you already have `master` checked out).
