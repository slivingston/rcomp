#!/bin/sh -e
# bootstrap rcomp server
#
# The ambition of this script is to fully prepare a Debian-like
# machine for running rcomp servers.
#
# NOTE that x509 certificates must be obtained and installed by you!
# You can obtain necessary files for free from the Let's Encrypt
# certificate authority (https://letsencrypt.org/).
#
# Guidance about configuring TLS can be found at
# https://wiki.mozilla.org/Security/Server_Side_TLS
# https://mozilla.github.io/server-side-tls/ssl-config-generator/

sudo apt-get -y update && sudo apt-get -y dist-upgrade
sudo apt-get -y install nginx
