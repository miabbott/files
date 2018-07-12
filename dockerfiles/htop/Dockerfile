FROM registry.fedoraproject.org/fedora:28
LABEL maintainer="Micah Abbott <miabbott@redhat.com>"
RUN dnf -y install htop && \
    dnf clean all
CMD ["htop"]
# sudo podman run -it --rm --pid=host localhost/miabbott/htop
