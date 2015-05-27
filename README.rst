sshoot
======

Command-line interface to manage multiple ``sshuttle`` VPN sessions.

`sshuttle <https://github.com/apenwarr/sshuttle>`_ creates a VPN connection
from your machine to any remote server that you can connect to via ssh.

``sshoot`` allows to define multiple VPN sessions using ``sshuttle`` and
start/stop them as needed.

It supports configuration options for most of ``sshuttle``'s features,
providing flexible configuration for profiles.


Typical usage
-------------

Create a profile::

  $ sshoot create -r host1.remote -HNd vpn1 10.0.0.0/24

Start the profile::

  $ sshoot start vpn1
  Profile started.

List existing profiles (active ones are marked)::

  $ sshoot list
       Profile  Remote host   Subnets
  --------------------------------------------
    *  vpn1     host1.remote  10.0.0.0/24
       vpn2     host2.remote  192.168.0.0/16
