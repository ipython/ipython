The IPython Notebook and its APIs by default will only be allowed to be
embedded in an iframe on the same origin.

To override this, set ``headers[X-Frame-Options]`` to one of

* DENY
* SAMEORIGIN
* ALLOW-FROM uri

See `Mozilla's guide to X-Frame-Options<https://developer.mozilla.org/en-US/docs/Web/HTTP/X-Frame-Options>`_ for more examples.
