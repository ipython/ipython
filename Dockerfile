FROM ipython/scipystack

MAINTAINER IPython Project <ipython-dev@scipy.org>

ADD . /srv/ipython/
WORKDIR /srv/ipython/

RUN pip2 install -e .[all]
RUN pip3 install -e .[all]

#RUN ipython2 kernelspec install-self
#RUN ipython3 kernelspec install-self

EXPOSE 8888

RUN echo "#!/bin/bash\nipython3 notebook --no-browser --port 8888 --ip=0.0.0.0" > /usr/local/bin/notebook.sh
RUN chmod a+x /usr/local/bin/notebook.sh

RUN useradd -m -s /bin/bash jupyter

USER jupyter
ENV HOME /home/jupyter
ENV SHELL /bin/bash
ENV USER jupyter

WORKDIR /home/jupyter/

CMD ["/usr/local/bin/notebook.sh"]
