"""Functions for Github authorisation."""
from __future__ import print_function

try:
    input = raw_input
except NameError:
    pass

import requests
import keyring
import getpass
import json

# Keyring stores passwords by a 'username', but we're not storing a username and
# password
fake_username = 'ipython_tools'

def get_auth_token():
    token = keyring.get_password('github', fake_username)
    if token is not None:
        return token
    
    print("Please enter your github username and password. These are not "
           "stored, only used to get an oAuth token. You can revoke this at "
           "any time on Github.")
    user = input("Username: ")
    pw = getpass.getpass("Password: ")
    
    auth_request = {
      "scopes": [
        "public_repo"
      ],
      "note": "IPython tools"
    }
    response = requests.post('https://api.github.com/authorizations',
                            auth=(user, pw), data=json.dumps(auth_request))
    response.raise_for_status()
    token = json.loads(response.text)['token']
    keyring.set_password('github', fake_username, token)
    return token

    
