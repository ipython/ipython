"""Functions for Github authorisation."""
from __future__ import print_function

try:
    input = raw_input
except NameError:
    pass

import requests
import getpass
import json

# Keyring stores passwords by a 'username', but we're not storing a username and
# password
fake_username = 'ipython_tools'

token = None
def get_auth_token():
    global token
    
    if token is not None:
        return token
    
    import keyring
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
        "public_repo",
        "gist"
      ],
      "note": "IPython tools",
      "note_url": "https://github.com/ipython/ipython/tree/master/tools",
    }
    response = requests.post('https://api.github.com/authorizations',
                            auth=(user, pw), data=json.dumps(auth_request))
    response.raise_for_status()
    token = json.loads(response.text)['token']
    keyring.set_password('github', fake_username, token)
    return token

def make_auth_header():
    return {'Authorization': 'token ' + get_auth_token()}

def post_issue_comment(project, num, body):
    url = 'https://api.github.com/repos/{project}/issues/{num}/comments'.format(project=project, num=num)
    payload = json.dumps({'body': body})
    r = requests.post(url, data=payload, headers=make_auth_header())

def post_gist(content, description='', filename='file', auth=False):
    """Post some text to a Gist, and return the URL."""
    post_data = json.dumps({
      "description": description,
      "public": True,
      "files": {
        filename: {
          "content": content
        }
      }
    }).encode('utf-8')
    
    headers = make_auth_header() if auth else {}
    response = requests.post("https://api.github.com/gists", data=post_data, headers=headers)
    response.raise_for_status()
    response_data = json.loads(response.text)
    return response_data['html_url']
    
def get_pull_request(project, num, github_api=3):
    """get pull request info  by number

    github_api : version of github api to use
    """
    if github_api==2 :
        url = "http://github.com/api/v2/json/pulls/{project}/{num}".format(project=project, num=num)
    elif github_api == 3:
        url = "https://api.github.com/repos/{project}/pulls/{num}".format(project=project, num=num)
    response = requests.get(url)
    response.raise_for_status()
    if github_api == 2 :
        return json.loads(response.text)['pull']
    return json.loads(response.text)

def get_pulls_list(project, github_api=3):
    """get pull request list

    github_api : version of github api to use
    """
    if github_api == 3 :
        url = "https://api.github.com/repos/{project}/pulls".format(project=project)
    else :
        url = "http://github.com/api/v2/json/pulls/{project}".format(project=project)
    response = requests.get(url)
    response.raise_for_status()
    if github_api == 2 :
        return json.loads(response.text)['pulls']
    return json.loads(response.text)
