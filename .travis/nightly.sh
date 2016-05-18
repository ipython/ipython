#!/bin/bas

if (( $TRAVIS_BRANCH == "$master" )) && (( "$TRAVIS_PULL_REQUEST" == 'false' )) && (( "$TRAVIS_REPO_SLUG" == "ipython/ipython" ));
then
  echo 'Building nightly release'
  python tools/build_release

  # decrypt .pypirc with credential for projectJupyter on testpypi and pypi. 
  echo 'Decrypting .pypirc ...'
  openssl aes-256-cbc -K $encrypted_669152acb59a_key -iv $encrypted_669152acb59a_iv -in .pypirc.enc -out .pypirc -d

  cp .pypirc ~/
  
  echo 'Installing twine'
  pip install twine

  echo 'Uploading nightly'
  twine upload dist/* -r $PYPI_REPOSITORY
else
  echo 'Not master,not ipython/ipython repo, or in a pull request: doing nothing.'
fi
