* Input transformers (see :doc:`/config/inputtransforms`) may now raise
  :exc:`SyntaxError` if they determine that input is invalid. The input
  transformation machinery in IPython will handle displaying the exception to
  the user and resetting state.
