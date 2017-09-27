
FROM registry.fedoraproject.org/fedora:26
LABEL maintainer="Micah Abbott <miabbott@redhat.com>"
RUN dnf -y install htop && \
    dnf clean all
CMD ["htop"]
