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
sudo apt-get -y install nginx redis-server supervisor python3-virtualenv
sudo nginx -s quit
sudo systemctl stop redis

python3 -m virtualenv -p python3 PY
source PY/bin/activate
pip install -U pip
pip install gunicorn aiohttp redis
