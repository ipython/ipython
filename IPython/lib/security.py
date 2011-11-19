"""
Password generation for the IPython notebook.
"""

import hashlib
import random
import getpass

# Length of the salt in nr of hex chars, which implies salt_len * 4
# bits of randomness.
salt_len = 12

def passwd(passphrase='', algorithm='sha1'):
    """Generate hashed password and salt for use in notebook configuration.

    In the notebook configuration, set `c.NotebookApp.password` to
    the generated string.

    Parameters
    ----------
    passphrase : str
        Password to hash.  If unspecified, the user is asked to input
        and verify a password.
    algorithm : str
        Hashing algorithm to use (e.g, 'sha1' or any argument supported
        by :func:`hashlib.new`).

    Returns
    -------
    hashed_passphrase : str
        Hashed password, in the format 'hash_algorithm:salt:passphrase_hash'.

    Examples
    --------
    In [1]: passwd('mypassword')
    Out[1]: 'sha1:7cf3:b7d6da294ea9592a9480c8f52e63cd42cfb9dd12'

    """
    if not passphrase:
        p0 = getpass.getpass('Enter password: ')
        p1 = getpass.getpass('Verify password: ')
        if (p0 == p1):
            passphrase = p0
        else:
            raise ValueError('Passwords did not match.')

    h = hashlib.new(algorithm)
    salt = ('%0' + str(salt_len) + 'x') % random.getrandbits(4 * salt_len)
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
    try:
        algorithm, salt, pw_digest = hashed_passphrase.split(':', 2)
    except (ValueError, TypeError):
        return False

    try:
        h = hashlib.new(algorithm)
    except ValueError:
        return False

    if len(pw_digest) == 0 or len(salt) != salt_len:
        return False

    h.update(passphrase + salt)

    return h.hexdigest() == pw_digest
