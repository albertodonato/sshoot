sshoot - Manage sshuttle VPN sessions
=====================================

|Latest Version| |Build Status| |Coverage Status|

Command-line interface to manage multiple sshuttle_ VPN sessions.

``sshuttle`` creates a VPN connection from your machine to any remote server
that you can connect to via ssh.

``sshoot`` allows to define multiple VPN sessions using ``sshuttle`` and
start/stop them as needed.

It supports configuration options for most of ``sshuttle``'s features,
providing flexible configuration for profiles.


Usage
-----

Create a profile:

.. code:: bash

    $ sshoot create -r host1.remote -HNd vpn1 10.0.0.0/24

Start it:

.. code:: bash

    $ sshoot start vpn1
    Profile started.

List existing profiles (active ones are marked):

.. code:: bash

    $ sshoot list
         Profile  Remote host   Subnets
    --------------------------------------------
      *  vpn1     host1.remote  10.0.0.0/24
         vpn2     host2.remote  192.168.0.0/16

Stop the profile:

.. code:: bash

    $ sshoot stop vpn1

Remove it:

.. code:: bash

    $ sshoot delete vpn1


.. _sshuttle: https://github.com/apenwarr/sshuttle

.. |Latest Version| image:: https://img.shields.io/pypi/v/sshoot.svg
   :target: https://pypi.python.org/pypi/sshoot
.. |Build Status| image:: https://img.shields.io/travis/albertodonato/sshoot.svg
   :target: https://travis-ci.org/albertodonato/sshoot
.. |Coverage Status| image:: https://img.shields.io/codecov/c/github/albertodonato/sshoot/master.svg
   :target: https://codecov.io/gh/albertodonato/sshoot
