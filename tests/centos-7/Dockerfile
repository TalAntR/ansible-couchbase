# CentOS 7 image to test ansible roles

FROM centos:7

MAINTAINER Anton Talevnin <talantr@gmail.com>

RUN yum update -y && yum -y install \
    openssl \
    sudo \
    systemd; \
    yum clean all

############################################################################################
# Enabling systemd
############################################################################################
ENV container docker

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in *; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
rm -f /lib/systemd/system/multi-user.target.wants/*;\
rm -f /etc/systemd/system/*.wants/*;\
rm -f /lib/systemd/system/local-fs.target.wants/*; \
rm -f /lib/systemd/system/sockets.target.wants/*udev*; \
rm -f /lib/systemd/system/sockets.target.wants/*initctl*; \
rm -f /lib/systemd/system/basic.target.wants/*;\
rm -f /lib/systemd/system/anaconda.target.wants/*;

VOLUME [ "/sys/fs/cgroup" ]

############################################################################################
# Configure SSH server and create ansible user
############################################################################################
RUN yum -y install openssh-server; \
    sed -ri 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config; \
    sed -i 's/#\?\s*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config;  \
    sed -i 's/#\?\s*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config; \
    systemctl enable sshd.service; \
    localedef -i en_US -f UTF-8 en_US.UTF-8; \
    getent passwd ansible >/dev/null || useradd -m -d /home/ansible -s /bin/bash ansible; \
    install -m 0700 -o ansible -g ansible -d /home/ansible/.ssh; \
    echo "ansible:$(openssl rand -base64 24)" | chpasswd; \
    echo "ansible ALL=(ALL:ALL) NOPASSWD: ALL" > /etc/sudoers.d/ansible

CMD ["/usr/sbin/init"]
