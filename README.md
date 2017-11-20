Couchbase cluster
=========


This is an Ansible role to setup Couchbase cluster. The collectd has a lot of configurable
plugins which provide powerfull capabilities. However you no need to use majority 
of them, so it's reasonable to have an Ansible role which give a chance to configure
selected plugins only. This code is an attempt to create such role.


Requirements
------------

This role has been tested with Ansible 2.2+ only. It's also supposed that
you are using the merge behaviour for variables (please, see about
[hash_behaviour=merge](http://docs.ansible.com/ansible/intro_configuration.html#hash-behaviour)
for details)


Role Variables
--------------

This role declares and uses the configurations variables in a hash under the
_collectd_ key (besides a variable collectd_version). This is a description 
for main variables which you may want to change.


  * _collectd_version_ is a desired version of collectd agent or plugins;

  * _collectd.plugins_ is a section to declare plugin settings which you want
    to use in your environment. There are a couple ways to define plugins. The first
    one allow to assign _true/false_ value:

        plugin-name: true or false

    if you wish to enable/disable plugin with default settings, for example to enable
    interface plugin just add this configuration:

        collectd:
          ...
          plugins:
            interface: true

    The second way provides an ability to redefine plugin settings:

        plugin-name:
          enabled: true or false
          file: a file where plugin configuration will be saved
          options:
            plugin options in YAML format

    See examples below how to declare different parts of collectd configuration in YAML
    format.

  * _collectd.service_ is a section to declare global settings for collectd
    agent;

Dependencies
------------

This role doesn't depend from other ansible roles


Example Playbook
----------------

An example of how to use collectd agent:

        - hosts: all
          roles:
            - role: collectd
              collectd_version: 5.7.1
              collectd:
                service:
                  options:
                    FQDNLookup: false
                plugins:

                  # Write configuration in graphite.conf file
                  write_graphite:
                    file: graphite
                    enabled: true
                    options:
                      Node "graphite":
                        Host: "graphite-dev.example.lo"
                        LogSendErrors: true
                        Port: "2103"
                        Prefix: "collectd."
                        Protocol: "tcp"
                        EscapeCharacter: "_"
                        SeparateInstances: true
                        StoreRates: false
                        AlwaysAppendDS: false

                  # Write configuration in main configuration file
                  network:
                    enabled: false
                    options:
                      Server:
                        - "collectd-server-01.example.lo	23451"
                        - "collectd-server-02.example.lo	23451"


Install collectd agent from EPEL repo for RHEL-based systems:


        - hosts: rhel
          roles:
            - role: collectd
              collectd_version: 5.7.1
              collectd:
                # EPEL repo is used for this installation
                providers:
                  pkg:
                    repositories:
                      Collectd:
                        enabled: no
                    prerequisites:
                      - epel-release
                    packages:
                      - collectd
                      - collectd-netlink

                service:
                  options:
                    FQDNLookup: false

                plugins:
                  # Reporting of physical memory usage
                  memory:
                    enabled: true
                    options:
                      ValuesAbsolute: true
                      ValuesPercentage: true

                  uptime:
                    enabled: true

                  write_graphite:
                    file: graphite
                    enabled: true
                    options:
                      Node "carbon-relay":
                        Host: "{{ graphite.host }}"
                        Port: "{{ graphite.port }}"
                        Prefix: "{{ graphite.prefix }}"
                        LogSendErrors: true
                        Protocol: "udp"
                        EscapeCharacter: "_"
                        SeparateInstances: true
                        StoreRates: false
                        AlwaysAppendDS: false


License
-------

MIT


Author Information
------------------

Anton Talevnin <talantr@gmail.com>
