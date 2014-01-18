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

import base64
from contextlib import contextmanager
import hashlib
from hmac import HMAC
import io
import os

from IPython.utils.py3compat import string_types, unicode_type, cast_bytes
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import Instance, Bytes, Enum

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


def check_notebook_signature(nb, secret, scheme):
    """Check a notebook's stored signature
    
    If a signature is stored in the notebook's metadata,
    a new signature is computed and compared with the stored value.
    
    Returns True if the signature is found and matches, False otherwise.
    
    The following conditions must all be met for a notebook to be trusted:
    - a signature is stored in the form 'scheme:hexdigest'
    - the stored scheme matches the requested scheme
    - the requested scheme is available from hashlib
    - the computed hash from notebook_signature matches the stored hash
    """
    stored_signature = nb['metadata'].get('signature', None)
    if not stored_signature \
        or not isinstance(stored_signature, string_types) \
        or ':' not in stored_signature:
        return False
    stored_scheme, sig = stored_signature.split(':', 1)
    if scheme != stored_scheme:
        return False
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


def mark_trusted_cells(nb, secret, scheme):
    """Mark cells as trusted if the notebook's signature can be verified
    
    Sets ``cell.trusted = True | False`` on all code cells,
    depending on whether the stored signature can be verified.
    """
    if not nb['worksheets']:
        # nothing to mark if there are no cells
        return True
    trusted = check_notebook_signature(nb, secret, scheme)
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


class NotebookNotary(LoggingConfigurable):
    """A class for configuring notebook signatures
    
    It stores the secret with which to sign notebooks,
    and the hashing scheme to use for notebook signatures.
    """
    
    scheme = Enum(hashlib.algorithms, default_value='sha256', config=True,
        help="""The hashing algorithm used to sign notebooks."""
    )
    
    profile_dir = Instance("IPython.core.profiledir.ProfileDir")
    def _profile_dir_default(self):
        from IPython.core.application import BaseIPythonApplication
        if BaseIPythonApplication.initialized():
            app = BaseIPythonApplication.instance()
        else:
            # create an app, without the global instance
            app = BaseIPythonApplication()
            app.initialize()
        return app.profile_dir
    
    secret = Bytes(config=True,
        help="""The secret key with which notebooks are signed."""
    )
    def _secret_default(self):
        # note : this assumes an Application is running
        profile_dir = self.profile_dir
        secret_file = os.path.join(profile_dir.security_dir, 'notebook_secret')
        if os.path.exists(secret_file):
            with io.open(secret_file, 'rb') as f:
                return f.read()
        else:
            secret = base64.encodestring(os.urandom(1024))
            self.log.info("Writing output secret to %s", secret_file)
            with io.open(secret_file, 'wb') as f:
                f.write(secret)
            try:
                os.chmod(secret_file, 0o600)
            except OSError:
                self.log.warn(
                    "Could not set permissions on %s",
                    secret_file
                )
            return secret

    