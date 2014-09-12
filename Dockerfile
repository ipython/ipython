# Designed to be run as 
# 
# docker run -it -p 9999:8888 ipython/latest

FROM ipython/scipystack

MAINTAINER IPython Project <ipython-dev@scipy.org>

ADD . /srv/ipython/
WORKDIR /srv/ipython/

RUN pip2 install fabric
RUN pip3 install jsonschema jsonpointer fabric

RUN pip2 install .
RUN pip3 install .

EXPOSE 8888

RUN echo "#!/bin/bash\nipython3 notebook --no-browser --port 8888 --ip=0.0.0.0" > /usr/local/bin/notebook.sh
RUN chmod a+x /usr/local/bin/notebook.sh

RUN useradd -m -s /bin/bash jupyter

USER jupyter
ENV HOME /home/jupyter
ENV SHELL /bin/bash
ENV USER jupyter

WORKDIR /home/jupyter/

RUN ipython2 kernelspec install-self
RUN ipython3 kernelspec install-self

CMD ["/usr/local/bin/notebook.sh"]
