## Current upstream pretty, does not (yet?) incorporate the changes to the
## local _pretty.py
#try:
#    from pretty import *
#    import pretty
#    _singleton_pprinters = pretty._singleton_pprinters
#    _type_pprinters = pretty._type_pprinters
#    _deferred_type_pprinters = pretty._deferred_type_pprinters
#except ImportError:
#    from _pretty import *
#    import _pretty
#    _singleton_pprinters = _pretty._singleton_pprinters
#    _type_pprinters = _pretty._type_pprinters
#    _deferred_type_pprinters = _pretty._deferred_type_pprinters
from _pretty import *
import _pretty
_singleton_pprinters = _pretty._singleton_pprinters
_type_pprinters = _pretty._type_pprinters
_deferred_type_pprinters = _pretty._deferred_type_pprinters
