# IPython Notebook development

# Development dependencies

Developers of the IPython Notebook will need to install the following tools:

* fabric
* node.js
* less (`npm install -g less`)
* bower (`npm install -g bower`)

# Components

We are moving to a model where our JavaScript dependencies are managed using 
[bower](http://bower.io/). These packages are installed in `static/components`
and commited into our git repo. Our dependencies are described in the file
`static/bower.json`. To update our bower packages, run `fab components` in this
directory.

Because CodeMirror does not use proper semantic versioning for its GitHub tags,
we maintain our own fork of CodeMirror that is used with bower. This fork should
track the upstream CodeMirror exactly; the only difference is that we are adding
semantic versioned tags to our repo.

# less

If you edit our `.less` files you will need to run the less compiler to build
our minified css files.  This can be done by running `fab css` from this directory.

