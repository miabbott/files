FROM docker.io/python:3
RUN pip3 install bpytop --upgrade
COPY bpytop.conf /etc/bpytop.conf
ENTRYPOINT /usr/local/bin/bpytop
