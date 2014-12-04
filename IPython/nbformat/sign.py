"""Functions for signing notebooks"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

import base64
from contextlib import contextmanager
import hashlib
from hmac import HMAC
import io
import os

from IPython.utils.io import atomic_writing
from IPython.utils.py3compat import string_types, unicode_type, cast_bytes
from IPython.utils.traitlets import Instance, Bytes, Enum, Any, Unicode, Bool
from IPython.config import LoggingConfigurable, MultipleInstanceError
from IPython.core.application import BaseIPythonApplication, base_flags

from . import read, write, NO_CONVERT

try:
    # Python 3
    algorithms = hashlib.algorithms_guaranteed
except AttributeError:
    algorithms = hashlib.algorithms


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

def yield_code_cells(nb):
    """Iterator that yields all cells in a notebook
    
    nbformat version independent
    """
    if nb.nbformat >= 4:
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                yield cell
    elif nb.nbformat == 3:
        for ws in nb['worksheets']:
            for cell in ws['cells']:
                if cell['cell_type'] == 'code':
                    yield cell

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


class NotebookNotary(LoggingConfigurable):
    """A class for computing and verifying notebook signatures."""
    
    profile_dir = Instance("IPython.core.profiledir.ProfileDir")
    def _profile_dir_default(self):
        from IPython.core.application import BaseIPythonApplication
        app = None
        try:
            if BaseIPythonApplication.initialized():
                app = BaseIPythonApplication.instance()
        except MultipleInstanceError:
            pass
        if app is None:
            # create an app, without the global instance
            app = BaseIPythonApplication()
            app.initialize(argv=[])
        return app.profile_dir
    
    algorithm = Enum(algorithms, default_value='sha256', config=True,
        help="""The hashing algorithm used to sign notebooks."""
    )
    def _algorithm_changed(self, name, old, new):
        self.digestmod = getattr(hashlib, self.algorithm)
    
    digestmod = Any()
    def _digestmod_default(self):
        return getattr(hashlib, self.algorithm)
    
    secret_file = Unicode(config=True,
        help="""The file where the secret key is stored."""
    )
    def _secret_file_default(self):
        if self.profile_dir is None:
            return ''
        return os.path.join(self.profile_dir.security_dir, 'notebook_secret')
    
    secret = Bytes(config=True,
        help="""The secret key with which notebooks are signed."""
    )
    def _secret_default(self):
        # note : this assumes an Application is running
        if os.path.exists(self.secret_file):
            with io.open(self.secret_file, 'rb') as f:
                return f.read()
        else:
            secret = base64.encodestring(os.urandom(1024))
            self._write_secret_file(secret)
            return secret
    
    def _write_secret_file(self, secret):
        """write my secret to my secret_file"""
        self.log.info("Writing notebook-signing key to %s", self.secret_file)
        with io.open(self.secret_file, 'wb') as f:
            f.write(secret)
        try:
            os.chmod(self.secret_file, 0o600)
        except OSError:
            self.log.warn(
                "Could not set permissions on %s",
                self.secret_file
            )
        return secret
    
    def compute_signature(self, nb):
        """Compute a notebook's signature
        
        by hashing the entire contents of the notebook via HMAC digest.
        """
        hmac = HMAC(self.secret, digestmod=self.digestmod)
        # don't include the previous hash in the content to hash
        with signature_removed(nb):
            # sign the whole thing
            for b in yield_everything(nb):
                hmac.update(b)
        
        return hmac.hexdigest()
    
    def check_signature(self, nb):
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
        if nb.nbformat < 3:
            return False
        stored_signature = nb['metadata'].get('signature', None)
        if not stored_signature \
            or not isinstance(stored_signature, string_types) \
            or ':' not in stored_signature:
            return False
        stored_algo, sig = stored_signature.split(':', 1)
        if self.algorithm != stored_algo:
            return False
        my_signature = self.compute_signature(nb)
        return my_signature == sig
    
    def sign(self, nb):
        """Sign a notebook, indicating that its output is trusted
        
        stores 'algo:hmac-hexdigest' in notebook.metadata.signature
        
        e.g. 'sha256:deadbeef123...'
        """
        if nb.nbformat < 3:
            return
        signature = self.compute_signature(nb)
        nb['metadata']['signature'] = "%s:%s" % (self.algorithm, signature)
    
    def mark_cells(self, nb, trusted):
        """Mark cells as trusted if the notebook's signature can be verified
        
        Sets ``cell.metadata.trusted = True | False`` on all code cells,
        depending on whether the stored signature can be verified.
        
        This function is the inverse of check_cells
        """
        if nb.nbformat < 3:
            return
        
        for cell in yield_code_cells(nb):
            cell['metadata']['trusted'] = trusted
    
    def _check_cell(self, cell, nbformat_version):
        """Do we trust an individual cell?
        
        Return True if:
        
        - cell is explicitly trusted
        - cell has no potentially unsafe rich output
        
        If a cell has no output, or only simple print statements,
        it will always be trusted.
        """
        # explicitly trusted
        if cell['metadata'].pop("trusted", False):
            return True
        
        # explicitly safe output
        if nbformat_version >= 4:
            safe = {'text/plain', 'image/png', 'image/jpeg'}
            unsafe_output_types = ['execute_result', 'display_data']
            safe_keys = {"output_type", "execution_count", "metadata"}
        else: # v3
            safe = {'text', 'png', 'jpeg'}
            unsafe_output_types = ['pyout', 'display_data']
            safe_keys = {"output_type", "prompt_number", "metadata"}
        
        for output in cell['outputs']:
            output_type = output['output_type']
            if output_type in unsafe_output_types:
                # if there are any data keys not in the safe whitelist
                output_keys = set(output)
                if output_keys.difference(safe_keys):
                    return False
        
        return True
    
    def check_cells(self, nb):
        """Return whether all code cells are trusted
        
        If there are no code cells, return True.
        
        This function is the inverse of mark_cells.
        """
        if nb.nbformat < 3:
            return False
        trusted = True
        for cell in yield_code_cells(nb):
            # only distrust a cell if it actually has some output to distrust
            if not self._check_cell(cell, nb.nbformat):
                trusted = False

        return trusted


trust_flags = {
    'reset' : (
        {'TrustNotebookApp' : { 'reset' : True}},
        """Generate a new key for notebook signature.
        All previously signed notebooks will become untrusted.
        """
    ),
}
trust_flags.update(base_flags)
trust_flags.pop('init')


class TrustNotebookApp(BaseIPythonApplication):
    
    description="""Sign one or more IPython notebooks with your key,
    to trust their dynamic (HTML, Javascript) output.
    
    Trusting a notebook only applies to the current IPython profile.
    To trust a notebook for use with a profile other than default,
    add `--profile [profile name]`.
    
    Otherwise, you will have to re-execute the notebook to see output.
    """
    
    examples = """
    ipython trust mynotebook.ipynb and_this_one.ipynb
    ipython trust --profile myprofile mynotebook.ipynb
    """
    
    flags = trust_flags
    
    reset = Bool(False, config=True,
        help="""If True, generate a new key for notebook signature.
        After reset, all previously signed notebooks will become untrusted.
        """
    )
    
    notary = Instance(NotebookNotary)
    def _notary_default(self):
        return NotebookNotary(parent=self, profile_dir=self.profile_dir)
    
    def sign_notebook(self, notebook_path):
        if not os.path.exists(notebook_path):
            self.log.error("Notebook missing: %s" % notebook_path)
            self.exit(1)
        with io.open(notebook_path, encoding='utf8') as f:
            nb = read(f, NO_CONVERT)
        if self.notary.check_signature(nb):
            print("Notebook already signed: %s" % notebook_path)
        else:
            print("Signing notebook: %s" % notebook_path)
            self.notary.sign(nb)
            with atomic_writing(notebook_path) as f:
                write(nb, f, NO_CONVERT)
    
    def generate_new_key(self):
        """Generate a new notebook signature key"""
        print("Generating new notebook key: %s" % self.notary.secret_file)
        self.notary._write_secret_file(os.urandom(1024))
    
    def start(self):
        if self.reset:
            self.generate_new_key()
            return
        if not self.extra_args:
            self.log.critical("Specify at least one notebook to sign.")
            self.exit(1)
        
        for notebook_path in self.extra_args:
            self.sign_notebook(notebook_path)

