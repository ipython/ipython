The completer Completion API has seen an overhaul. The old
``Completer.complete()`` API is waiting deprecation and will soon be replaced
by the ``Completer.completions()`` one. While the ``Completer.complete()`` API
was assuming completions would all replace the same range of text in the
completed buffer, ``Completer.completions()`` does not. To smooth the transition
we provide two utility methods ``regulrize...`` and ``stufff`` which can
partially adapt between the old and new API. The new API is marked as
"unstable" and can only be use explicitly when called from within a decorator
we provide.
