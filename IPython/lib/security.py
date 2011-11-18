"""
Password generation for the IPython notebook.
"""

import hashlib
import random

def passwd(passphrase):
    """Generate hashed password and salt for use in notebook configuration.

    In the notebook configuration, set `c.NotebookApp.password` to
    the generated string.

    Parameters
    ----------
    passphrase : str
        Password to hash.

    Returns
    -------
    hashed_passphrase : str
        Hashed password, in the format 'hash_algorithm:salt:passphrase_hash'.

    Examples
    --------
    In [1]: passwd('mypassword')
    Out[1]: 'sha1:7cf3:b7d6da294ea9592a9480c8f52e63cd42cfb9dd12'

    """
    algorithm = 'sha1'

    h = hashlib.new(algorithm)
    salt = hex(int(random.getrandbits(16)))[2:]
    h.update(passphrase + salt)

    return ':'.join((algorithm, salt, h.hexdigest()))

def passwd_check(hashed_passphrase, passphrase):
    """Verify that a given passphrase matches its hashed version.

    Parameters
    ----------
    hashed_passphrase : str
        Hashed password, in the format returned by `passwd`.
    passphrase : str
        Passphrase to validate.

    Returns
    -------
    valid : bool
        True if the passphrase matches the hash.

    Examples
    --------
    In [1]: from IPython.lib.security import passwd_check

    In [2]: passwd_check('sha1:7cf3:b7d6da294ea9592a9480c8f52e63cd42cfb9dd12',
       ...:              'mypassword')
    Out[2]: True

    In [3]: passwd_check('sha1:7cf3:b7d6da294ea9592a9480c8f52e63cd42cfb9dd12',
       ...:              'anotherpassword')
    Out[3]: False

    """
    # Algorithm and hash length
    supported_algorithms = {'sha1': 40}

    try:
        algorithm, salt, pw_digest = hashed_passphrase.split(':', 2)
    except (ValueError, TypeError):
        return False

    if not (algorithm in supported_algorithms and \
            len(pw_digest) == supported_algorithms[algorithm] and \
            len(salt) == 4):
        return False

    h = hashlib.new(algorithm)
    h.update(passphrase + salt)

    return h.hexdigest() == pw_digest
