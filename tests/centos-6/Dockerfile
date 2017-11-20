# CentOS 6 image to test ansible roles

FROM centos:centos6
MAINTAINER Anton Talevnin <talantr@gmail.com>

RUN yum update -y && yum -y install \
    openssl \
    openssh-server \
    sudo

############################################################################################
# Configure SSH server
RUN sed -ri 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config; \
    sed -i 's/#\?\s*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config; \
    sed -i 's/#\?\s*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config; \
    service sshd start; \
    mkdir /var/run/sshd; \
    localedef -i en_US -f UTF-8 en_US.UTF-8; \
    getent passwd ansible >/dev/null || useradd -m -d /home/ansible -s /bin/bash ansible; \
    install -m 0700 -o ansible -g ansible -d /home/ansible/.ssh; \
    echo "ansible:$(openssl rand -base64 24)" | chpasswd; \
    echo "ansible ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/ansible

CMD ["/usr/sbin/sshd", "-D"]