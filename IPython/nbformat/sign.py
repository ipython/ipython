"""Functions for signing notebooks"""
#-----------------------------------------------------------------------------
#  Copyright (C) 2014, The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

from contextlib import contextmanager
import hashlib
from hmac import HMAC

from IPython.utils.py3compat import string_types, unicode_type, cast_bytes

#-----------------------------------------------------------------------------
# Code
#-----------------------------------------------------------------------------


def yield_everything(obj):
    """Yield every item in a container as bytes
    
    Allows any JSONable object to be passed to an HMAC digester
    without having to serialize the whole thing.
    """
    if isinstance(obj, dict):
        for key in sorted(obj):
            value = obj[key]
            yield cast_bytes(key)
            for b in yield_everything(value):
                yield b
    elif isinstance(obj, (list, tuple)):
        for element in obj:
            for b in yield_everything(element):
                yield b
    elif isinstance(obj, unicode_type):
        yield obj.encode('utf8')
    else:
        yield unicode_type(obj).encode('utf8')


@contextmanager
def signature_removed(nb):
    """Context manager for operating on a notebook with its signature removed
    
    Used for excluding the previous signature when computing a notebook's signature.
    """
    save_signature = nb['metadata'].pop('signature', None)
    try:
        yield
    finally:
        if save_signature is not None:
            nb['metadata']['signature'] = save_signature


def notebook_signature(nb, secret, scheme):
    """Compute a notebook's signature
    
    by hashing the entire contents of the notebook via HMAC digest.
    scheme is the hashing scheme, which must be an attribute of the hashlib module,
    as listed in hashlib.algorithms.
    """
    hmac = HMAC(secret, digestmod=getattr(hashlib, scheme))
    # don't include the previous hash in the content to hash
    with signature_removed(nb):
        # sign the whole thing
        for b in yield_everything(nb):
            hmac.update(b)
        
    return hmac.hexdigest()


def check_notebook_signature(nb, secret):
    """Check a notebook's stored signature
    
    If a signature is stored in the notebook's metadata,
    a new signature is computed using the same hashing scheme,
    and compared.
    
    If no signature can be found, or the scheme of the existing signature is unavailable,
    it will return False.
    """
    stored_signature = nb['metadata'].get('signature', None)
    if not stored_signature \
        or not isinstance(stored_signature, string_types) \
        or ':' not in stored_signature:
        return False
    scheme, sig = stored_signature.split(':', 1)
    try:
        my_signature = notebook_signature(nb, secret, scheme)
    except AttributeError:
        return False
    return my_signature == sig


def trust_notebook(nb, secret, scheme):
    """Re-sign a notebook, indicating that its output is trusted
    
    stores 'scheme:hmac-hexdigest' in notebook.metadata.signature
    
    e.g. 'sha256:deadbeef123...'
    """
    signature = notebook_signature(nb, secret, scheme)
    nb['metadata']['signature'] = "%s:%s" % (scheme, signature)


def mark_trusted_cells(nb, secret):
    """Mark cells as trusted if the notebook's signature can be verified
    
    Sets ``cell.trusted = True | False`` on all code cells,
    depending on whether the stored signature can be verified.
    """
    if not nb['worksheets']:
        # nothing to mark if there are no cells
        return True
    trusted = check_notebook_signature(nb, secret)
    for cell in nb['worksheets'][0]['cells']:
        if cell['cell_type'] == 'code':
            cell['trusted'] = trusted
    return trusted


def check_trusted_cells(nb):
    """Return whether all code cells are trusted
    
    If there are no code cells, return True.
    """
    if not nb['worksheets']:
        return True
    for cell in nb['worksheets'][0]['cells']:
        if cell['cell_type'] != 'code':
            continue
        if not cell.get('trusted', False):
            return False
    return True

        