FROM registry.fedoraproject.org/fedora:26
LABEL maintainer="Micah Abbott <miabbott@redhat.com>"
ENV container=docker
RUN dnf -y install flatpak-builder \
                   fuse \
                   git \
		   git-review \
                   iputils \
                   man \
                   python2-virtualenv \
                   python3-virtualenv \
                   redhat-rpm-config \
                   sudo \
                   vim && \
    dnf clean all

RUN echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    echo "Defaults secure_path = /usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> /etc/sudoers && \
    useradd --groups wheel --uid 1000 miabbott

USER miabbott

CMD ["/bin/bash"]
