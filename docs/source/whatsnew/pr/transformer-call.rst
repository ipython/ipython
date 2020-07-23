Input transformers are now called only once in the execution path of `InteractiveShell`, allowing to register
transformer that potentially have side effects (note that this is not recommended). `should_run_async`, and
`run_cell_async` now take a recommended optional `transformed_cell`, and `preprocessing_exc_tuple` parameters that will
become mandatory at some point in the future; that is to say cells need to be explicitly transformed to be valid Python
syntax ahead of trying to run them. :ghpull:`12440`
