# sshoot - Manage sshuttle VPN sessions

[![Latest Version](https://img.shields.io/pypi/v/sshoot.svg)](https://pypi.python.org/pypi/sshoot)
[![Build Status](https://travis-ci.org/albertodonato/sshoot.svg?branch=master)](https://travis-ci.org/albertodonato/sshoot)
[![Coverage Status](https://codecov.io/gh/albertodonato/sshoot/branch/master/graph/badge.svg)](https://codecov.io/gh/albertodonato/sshoot)

Command-line interface to manage multiple [`sshuttle`](https://github.com/apenwarr/sshuttle) VPN sessions.

`sshuttle` creates a VPN connection from your machine to any remote server that
you can connect to via ssh.

`sshoot` allows to define multiple VPN sessions using `sshuttle` and start/stop
them as needed.

It supports configuration options for most of `sshuttle`'s features, providing
flexible configuration for profiles.


## Typical usage

Create a profile:

```bash
$ sshoot create -r host1.remote -HNd vpn1 10.0.0.0/24
```

Start the profile:

```bash
$ sshoot start vpn1
Profile started.
```

List existing profiles (active ones are marked):

```bash
$ sshoot list
     Profile  Remote host   Subnets
--------------------------------------------
  *  vpn1     host1.remote  10.0.0.0/24
     vpn2     host2.remote  192.168.0.0/16
```
