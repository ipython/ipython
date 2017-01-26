The completer Completion API has seen an overhaul. The old
``Completer.complete()`` API is waiting deprecation and will soon be replaced
by ``Completer.completions()``.

This new API is capable of pulling completions from :any:`jedi`, thus allowing
type inference on non-executed code. If :any:`jedi` is installed completion
like the following are now becoming possible without code evaluation:

   >>> data = ['Number of users', 123_456]
   ... data[0].<tab>

IPython is now capable of inferring that `data[0]` is a string, and will
suggest completions like `.capitalize`. The completion power of IPython will
increase with new Jedi releases, and a number of bugs and more completions are
already available on development version of :any:`jedi` if you are curious.

User of the prompt_toolkit interface should also see the type of the item they
are selecting (method, attribute, module, keyword ...).

The use of Jedi also full fill a number of request and fix a number of bugs
like case insensitive completion, completion after division operator: See
:ghpull:`ipython/ipython#10182`.

Extra patches and updates will be needed to the :any:`ipykernel` package for
this feature to be available for this to be available to other clients like
Notebook, Lab, Nteract, Hydrogen...
