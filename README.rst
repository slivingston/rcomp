Introduction
------------

**rcomp** is a proof-of-concept for facilitating reproducible research by
running primary assets remotely and collecting results by locally using a pure
Python program.


Organization
------------

Source code for the server is in the directory ``serv/``. Note that it is
collectively referred to as **the server**, but in general it can be deployed
over multiple hosts, e.g., with reverse proxies that load balance across hosts
that have ``rcompserv`` processes.

Source code for clients are in the directory ``frontend/``. They are
approximately sorted according to programming language, e.g., the directory
``py/`` contains a client library in Python. Note that some clients have Web
UIs, so their installation and execution involve "backend" components, e.g.,
nginx configurations.


License
-------

This is free software released under the terms of `the BSD 3-Clause License
<https://opensource.org/licenses/BSD-3-Clause>`_.  There is no warranty; not even
for merchantability or fitness for a particular purpose.  Consult LICENSE.txt
for copying conditions.
