input_transformers can now have an attribute ``has_side_effects`` set to `True`, which will prevent the
transformers from being ran when IPython is trying to guess whether the user input is complete.
