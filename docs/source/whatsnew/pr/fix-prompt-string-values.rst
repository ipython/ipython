Preserve string values during prompt removal
--------------------------------------------

Classic Python prompt removal now uses Python's tokenizer to identify strings.
Prompt characters inside assigned multiline strings, raw strings, bytes
literals, and f-strings are preserved. Python 3.14 template strings are also
supported. Comments, escaped delimiters, and incomplete strings no longer
depend on a triple-quote regular-expression heuristic.

When a string starts on a prompted line, IPython removes one outer prompt
layer from the pasted code. This also corrects prompted bare string
expressions that previously retained their outer prompts. Mixed pastes retain
the indentation context of the enclosing code block.
