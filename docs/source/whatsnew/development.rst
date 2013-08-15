=====================
 Development version
=====================

This document describes in-flight development work.


Backwards incompatible changes
------------------------------

* Python 2.6 and 3.2 are no longer supported: the minimum required
  Python versions are now 2.7 and 3.3.
* The `call` methods for nbconvert transformers has been renamed to
  `transform`.
* The `call` methods of nbconvert post-processsors have been renamed to
  `postprocess`.
