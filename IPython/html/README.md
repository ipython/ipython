# IPython Notebook development

## Development dependencies

Developers of the IPython Notebook will need to install the following tools:

* fabric
* node.js
* less (`npm install -g less`)
* bower (`npm install -g bower`)

## Components

We are moving to a model where our JavaScript dependencies are managed using 
[bower](http://bower.io/). These packages are installed in `static/components`
and commited into our git repo. Our dependencies are described in the file
`static/bower.json`. To update our bower packages, run `fab components` in this
directory.

Because CodeMirror does not use proper semantic versioning for its GitHub tags,
we maintain our own fork of CodeMirror that is used with bower. This fork should
track the upstream CodeMirror exactly; the only difference is that we are adding
semantic versioned tags to our repo.

## less

If you edit our `.less` files you will need to run the less compiler to build
our minified css files.  This can be done by running `fab css` from this directory.

## JavaScript Documentation


How to  Build/ view the doc  for JavaScript. JavaScript documentation  should follow a
style close  to JSDoc  one, so you  should be  able to build  them with  your favorite
documentation builder. Still  the documentation comment are mainly written  to be read
with YUI  doc. You can either  build a static version,  or start a YUIdoc  server that
will live update the doc at every page request.



To do so, you will need to install YUIdoc.

### Install NodeJS

Node is a browser less javascript interpreter. To install it please refer to
the documentation for your platform. Install also NPM (node package manager) if
it does not come bundled with it.  

### Get YUIdoc

npm does by default install package in `./node_modules` instead of doing a
system wide install. I'll leave you to yuidoc docs if you want to make a system
wide install.

First, cd into js directory :
```bash
cd IPython/html/notebook/static/js/
# install yuidoc
npm install yuidocjs
```


### Run YUIdoc server

From IPython/html/notebook/static/js/
```bash
# run yuidoc for install dir 
./node_modules/yuidocjs/lib/cli.js --server .
```

Follow the instruction and the documentation should be available on localhost:3000

Omitting `--server` will build a static version in the `out` folder by default.
