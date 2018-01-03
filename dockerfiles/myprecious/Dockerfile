FROM registry.fedoraproject.org/fedora:27
LABEL maintainer="Micah Abbott <miabbott@redhat.com>"
ENV container=docker
RUN sed -i '/tsflags=nodocs/d' /etc/dnf/dnf.conf && \
    dnf -y reinstall '*' && \
    dnf -y install flatpak-builder \
                   fuse \
                   gcc \
                   git \
                   git-review \
                   iputils \
                   man \
                   python2-virtualenv \
                   python3-virtualenv \
                   redhat-rpm-config \
                   rsync \
                   sshpass \
                   sudo \
                   vim && \
    dnf clean all

RUN echo "%wheel ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    echo "Defaults secure_path = /usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin" >> /etc/sudoers && \
    useradd --groups wheel --uid 1000 miabbott

USER miabbott

CMD ["/bin/bash"]
