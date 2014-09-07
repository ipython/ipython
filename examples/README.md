![IPython Logo](images/ipython_logo.png)

This directory/container contains [IPython's notebook-based documentation](http://nbviewer.ipython.org/github/ipython/ipython/blob/master/examples/Index.ipynb). This augments our [Sphinx-based documentation](http://ipython.org/ipython-doc/stable/index.html) with notebooks that contain interactive tutorials and examples. Over time, more of our documentation will be pulled into this format.

This set of notebooks is also available as a Docker image with Python dependencies so you can try out the example notebooks without installing each set of packages manually. It relies on the [ipython/scipyserver Docker image](https://registry.hub.docker.com/u/ipython/scipyserver/). To run, you'll need to [install and configure Docker](https://docs.docker.com/installation/) then:

```
docker run -e "PASSWORD=SetYourPassword" -p 9999:8888 ipython/examples
```

This will run the IPython Notebook server on port 9999 on the Docker host.
